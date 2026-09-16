from dataclasses import dataclass


@dataclass(frozen=True)
class Driver:
    id: int
    nome: str
    ativo: bool


@dataclass(frozen=True)
class ServiceType:
    id: int
    descricao: str
    ativo: bool


@dataclass(frozen=True)
class ReimbursementItem:
    tipo_servico_id: int
    tipo_servico_descricao: str
    os: str
    valor_centavos: int


@dataclass(frozen=True)
class Reimbursement:
    id: int
    numero: str
    motorista_id: int | None
    motorista_nome: str
    data_hora: str
    valor_total_centavos: int
    pdf_path: str | None
