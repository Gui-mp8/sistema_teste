from pydantic import BaseModel, PositiveFloat, PositiveInt, field_validator
import re
from datetime import datetime

class Contrato(BaseModel):
    cpf: str
    inicio_contrato: datetime
    valor_contrato: PositiveFloat
    qtd_funcionarios: PositiveInt

    @field_validator('cpf')
    def cpf_must_be_valid(cls, v):
        # Exemplo simples de validação de CPF
        if not re.fullmatch(r'\d{11}', v):
            raise ValueError('CPF deve conter 11 dígitos numéricos')
        return v
