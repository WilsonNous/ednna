import json
from pathlib import Path

import pytest

from ednna.specialists.protocol import (
    CONTRACT_VERSION,
    UnsupportedContractVersionError,
    validate_contract_version,
)


def test_contract_schema_is_valid_json_and_declares_v1():
    path = Path("contracts/intelligence-v1.schema.json")
    schema = json.loads(path.read_text(encoding="utf-8"))

    request = schema["$defs"]["IntelligenceRequest"]
    response = schema["$defs"]["IntelligenceResponse"]

    assert request["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert response["properties"]["contract_version"]["const"] == CONTRACT_VERSION


def test_contract_version_accepts_current_or_absent_transitional_version():
    validate_contract_version(CONTRACT_VERSION)
    validate_contract_version(None)


def test_contract_version_rejects_explicit_incompatible_version():
    with pytest.raises(UnsupportedContractVersionError):
        validate_contract_version("2")
