import json
import logging
import os
import time
from typing import Any
from uuid import UUID

import pika

from .classifier import IFRS18Classifier

REQUEST_QUEUE = "financial.classification.requests"
RESULT_QUEUE = "financial.classification.results"
DEAD_LETTER_EXCHANGE = "financial.classification.dead"
DEAD_LETTER_QUEUE = "financial.classification.results.dead"
LOGGER = logging.getLogger("laya_classifier.worker")


def classify_request(
    request: dict[str, Any], classifier: IFRS18Classifier
) -> dict[str, Any]:
    request_id = str(UUID(str(request.get("requestId", ""))))
    account_id = str(UUID(str(request.get("accountId", ""))))
    description = next(
        (
            value.strip()
            for key in ("description", "accountName", "accountCode")
            if isinstance(value := request.get(key), str) and value.strip()
        ),
        "",
    )

    if not description:
        return _review_result(
            request_id,
            account_id,
            "A conta não possui descrição para classificação; revisão manual necessária.",
        )

    try:
        classification = classifier.classify(description)
    except Exception:
        LOGGER.exception("Classifier failed for account %s", account_id)
        return _review_result(
            request_id,
            account_id,
            "O modelo não conseguiu classificar a conta; revisão manual necessária.",
        )

    needs_review = classification.needs_review
    category = classification.category.value if classification.category else None
    rationale = (
        "Sugestão automática com baixa confiança ou contexto insuficiente; revisar."
        if needs_review
        else "Sugestão automática do Laya; validar conforme o contexto da entidade."
    )

    return {
        "requestId": request_id,
        "accountId": account_id,
        "category": category,
        "confidence": classification.confidence,
        "rationale": rationale,
        "classifierName": "laya-classifier",
        "modelVersion": os.getenv("CLASSIFIER_MODEL_VERSION", "laya-router"),
        "needsReview": needs_review,
    }


def _review_result(request_id: str, account_id: str, rationale: str) -> dict[str, Any]:
    return {
        "requestId": request_id,
        "accountId": account_id,
        "category": None,
        "confidence": None,
        "rationale": rationale,
        "classifierName": "laya-classifier",
        "modelVersion": os.getenv("CLASSIFIER_MODEL_VERSION", "laya-router"),
        "needsReview": True,
    }


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    classifier = IFRS18Classifier()
    parameters = pika.URLParameters(
        os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    )

    while True:
        connection = None
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=REQUEST_QUEUE, durable=True)
            channel.exchange_declare(
                exchange=DEAD_LETTER_EXCHANGE,
                exchange_type="direct",
                durable=True,
            )
            channel.queue_declare(queue=DEAD_LETTER_QUEUE, durable=True)
            channel.queue_bind(
                queue=DEAD_LETTER_QUEUE,
                exchange=DEAD_LETTER_EXCHANGE,
                routing_key=DEAD_LETTER_QUEUE,
            )
            channel.queue_declare(
                queue=RESULT_QUEUE,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DEAD_LETTER_EXCHANGE,
                    "x-dead-letter-routing-key": DEAD_LETTER_QUEUE,
                },
            )
            channel.confirm_delivery()
            channel.basic_qos(prefetch_count=1)

            def handle_message(channel, method, properties, body) -> None:
                try:
                    request = json.loads(body)
                    if not isinstance(request, dict):
                        raise ValueError("Request payload must be a JSON object.")
                    result = classify_request(request, classifier)
                    published = channel.basic_publish(
                        exchange="",
                        routing_key=RESULT_QUEUE,
                        body=json.dumps(result).encode("utf-8"),
                        properties=pika.BasicProperties(
                            content_type="application/json",
                            delivery_mode=pika.DeliveryMode.Persistent,
                            message_id=result["requestId"],
                        ),
                        mandatory=True,
                    )
                    if published is False:
                        raise RuntimeError("RabbitMQ did not confirm the result message.")
                except (json.JSONDecodeError, TypeError, ValueError, KeyError) as error:
                    LOGGER.error("Rejecting invalid classification request: %s", error)
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return
                except Exception:
                    LOGGER.exception("Could not publish classification result; retrying request.")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    return

                channel.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue=REQUEST_QUEUE,
                on_message_callback=handle_message,
                auto_ack=False,
            )
            LOGGER.info("Consuming classification requests from %s", REQUEST_QUEUE)
            channel.start_consuming()
        except KeyboardInterrupt:
            LOGGER.info("Classification worker stopped.")
            return
        except pika.exceptions.AMQPError:
            LOGGER.exception("RabbitMQ is unavailable; reconnecting in five seconds.")
            time.sleep(5)
        finally:
            if connection is not None and connection.is_open:
                connection.close()