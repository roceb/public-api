import time

from src.app.views.input.report import Detection
from src.core.kafka.engine import AioKafkaEngine
import logging

logger = logging.getLogger(__name__)


class Report:
    def __init__(self, kafka_engine: AioKafkaEngine) -> None:
        self.kafka_engine = kafka_engine
        pass

    def _check_data_size(self, data: list[Detection]) -> list[Detection] | None:
        return None if len(data) > 5000 else data

    def _filter_valid_time(self, data: list[Detection]) -> list[Detection]:
        current_time = int(time.time())
        min_ts = current_time - 25200
        max_ts = current_time + 3600
        return [d for d in data if min_ts < d.ts < max_ts]

    def _check_unique_reporter(self, data: list[Detection]) -> list[Detection] | None:
        return None if len(set(d.reporter for d in data)) > 1 else data

    async def parse_data(self, data: list[dict]) -> list[Detection] | None:
        """
        Parse and validate a list of detection data.
        """
        data = self._check_data_size(data)
        if not data:
            logger.warning("invalid data size")
            return None

        data = self._filter_valid_time(data)
        if not data:
            logger.warning("invalid time")
            return None

        data = self._check_unique_reporter(data)
        if not data:
            logger.warning("invalid unique reporter")
            return None
        return data

    async def send_to_kafka(self, data: list[Detection]) -> None:
        for detection in data:
            detection = detection.model_dump_json()
            self.kafka_engine.message_queue.put_nowait(detection)
        return
