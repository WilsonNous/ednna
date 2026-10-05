from ednna.orchestration.contracts import Capability, OperationKind, SpecialistDescriptor


EDDY_DESCRIPTOR = SpecialistDescriptor(
    specialist_id="eddy",
    name="EDDY",
    domain="edi",
    description="Especialista operacional em EDI da Netunna.",
    capabilities=(
        Capability(
            name="edi.status.get",
            kind=OperationKind.QUERY,
            description="Consultar o estado geral da operação EDI.",
        ),
        Capability(
            name="edi.issue.inspect",
            kind=OperationKind.QUERY,
            description="Consultar e interpretar um chamado EDI.",
        ),
        Capability(
            name="edi.player.inspect",
            kind=OperationKind.QUERY,
            description="Consultar contexto operacional de um player EDI.",
        ),
        Capability(
            name="edi.rule.list",
            kind=OperationKind.QUERY,
            description="Listar regras EDI e seus estados de aprendizagem/homologação.",
        ),
        Capability(
            name="edi.operation.execute",
            kind=OperationKind.ACTION,
            description="Executar uma operação EDI previamente autorizada e idempotente.",
        ),
    ),
)
