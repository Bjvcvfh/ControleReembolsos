import csv
from datetime import datetime
from pathlib import Path

from database.database import get_connection
from utils.currency import format_decimal_csv


class ExportService:
    def export_history_csv(self, path: Path) -> Path:
        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    r.numero,
                    r.data_hora,
                    r.motorista_nome,
                    i.tipo_servico_descricao,
                    i.data_servico,
                    i.placa,
                    i.os,
                    i.valor_centavos,
                    r.valor_total_centavos
                FROM reembolsos r
                JOIN reembolso_itens i ON i.reembolso_id = r.id
                ORDER BY r.data_hora DESC, r.id DESC, i.id
                """
            ).fetchall()

        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(
                [
                    "numero_reembolso",
                    "data",
                    "hora",
                    "motorista",
                    "placa",
                    "tipo_servico",
                    "data_servico",
                    "os",
                    "valor_item",
                    "valor_total_reembolso",
                ]
            )
            for row in rows:
                dt = datetime.fromisoformat(row["data_hora"])
                service_date = ""
                if row["data_servico"]:
                    service_date = datetime.strptime(row["data_servico"], "%Y-%m-%d").strftime("%d/%m/%Y")
                writer.writerow(
                    [
                        row["numero"],
                        dt.strftime("%d/%m/%Y"),
                        dt.strftime("%H:%M"),
                        row["motorista_nome"],
                        row["placa"] or "",
                        row["tipo_servico_descricao"],
                        service_date,
                        row["os"] or "",
                        format_decimal_csv(row["valor_centavos"]),
                        format_decimal_csv(row["valor_total_centavos"]),
                    ]
                )
        return path
