def validate_result(result):
    required = ["status", "summary", "findings", "missing_information"]
    return (
        isinstance(result, dict)
        and all(k in result for k in required)
        and isinstance(result.get("findings"), list)
    )
