from src.utils.logger import get_logger


logger = get_logger(
    __name__
)


def handle_event(
    result: dict,
) -> None:

    logger.info(
        "Transaction decision=%s risk_score=%s",
        result.get("decision"),
        result.get("risk_score"),
    )