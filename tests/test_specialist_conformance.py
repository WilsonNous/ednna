from ednna.orchestration.contracts import (
    Capability,
    OperationKind,
    SpecialistDescriptor,
)
from ednna.specialists.conformance import SpecialistConformanceValidator
from ednna.specialists.manifest import (
    SpecialistManifest,
    SpecialistTransportManifest,
)


def test_valid_specialist_manifest_passes_conformance():
    manifest = SpecialistManifest(
        descriptor=SpecialistDescriptor(
            specialist_id="finance",
            name="Finance",
            domain="finance",
            description="Especialista financeiro",
            capabilities=(
                Capability(
                    name="finance.exposure.get",
                    kind=OperationKind.QUERY,
                    description="Consultar exposição financeira.",
                ),
            ),
        ),
        transport=SpecialistTransportManifest(
            base_url_env="FINANCE_BASE_URL",
            api_token_env="FINANCE_API_TOKEN",
            timeout_env="FINANCE_TIMEOUT_SECONDS",
        ),
    )

    report = SpecialistConformanceValidator().validate(manifest)

    assert report.valid is True
    assert report.issues == ()


def test_manifest_rejects_capability_outside_declared_domain():
    manifest = SpecialistManifest(
        descriptor=SpecialistDescriptor(
            specialist_id="finance",
            name="Finance",
            domain="finance",
            description="Especialista financeiro",
            capabilities=(
                Capability(
                    name="edi.operation.execute",
                    kind=OperationKind.ACTION,
                    description="Wrong domain",
                ),
            ),
        )
    )

    report = SpecialistConformanceValidator().validate(manifest)

    assert report.valid is False
    assert any(
        issue.code == "capability_domain_mismatch"
        for issue in report.issues
    )


def test_manifest_rejects_duplicate_capability_and_invalid_env_name():
    capability = Capability(
        name="finance.exposure.get",
        kind=OperationKind.QUERY,
        description="Consultar exposição financeira.",
    )
    manifest = SpecialistManifest(
        descriptor=SpecialistDescriptor(
            specialist_id="finance",
            name="Finance",
            domain="finance",
            description="Especialista financeiro",
            capabilities=(capability, capability),
        ),
        transport=SpecialistTransportManifest(
            base_url_env="finance-base-url",
            api_token_env="FINANCE_API_TOKEN",
        ),
    )

    report = SpecialistConformanceValidator().validate(manifest)

    codes = {issue.code for issue in report.issues}
    assert "duplicate_capability" in codes
    assert "invalid_transport_env" in codes


def test_registry_rejects_non_conformant_manifest():
    import pytest

    from ednna.orchestration.registry import SpecialistRegistry
    from ednna.specialists.catalog import (
        SpecialistConformanceError,
        register_catalog,
    )

    manifest = SpecialistManifest(
        descriptor=SpecialistDescriptor(
            specialist_id="Finance Agent",
            name="Finance",
            domain="finance",
            description="Invalid id",
            capabilities=(
                Capability(
                    name="finance.exposure.get",
                    kind=OperationKind.QUERY,
                    description="Consultar exposição.",
                ),
            ),
        )
    )

    with pytest.raises(SpecialistConformanceError):
        register_catalog(SpecialistRegistry(), (manifest,))
