from datetime import datetime

from database.database import get_connection, transaction


class ReimbursementService:
    def create_reimbursement(self, motorista_id: int, items: list[dict]) -> dict:
        if not motorista_id:
            raise ValueError("Selecione um motorista.")
        if not items:
            raise ValueError("Adicione pelo menos um item.")

        with transaction() as conn:
            driver = conn.execute(
                "SELECT id, nome FROM motoristas WHERE id = ? AND ativo = 1",
                (motorista_id,),
            ).fetchone()
            if not driver:
                raise ValueError("Motorista ativo nao encontrado.")

            prepared_items: list[dict] = []
            total = 0
            for item in items:
                service_type_id = int(item.get("tipo_servico_id") or 0)
                value_cents = int(item.get("valor_centavos") or 0)
                if service_type_id <= 0:
                    raise ValueError("Todos os itens precisam de tipo de servico.")
                if value_cents <= 0:
                    raise ValueError("Todos os itens precisam de valor maior que zero.")
                service_type = conn.execute(
                    "SELECT id, descricao FROM tipos_servico WHERE id = ? AND ativo = 1",
                    (service_type_id,),
                ).fetchone()
                if not service_type:
                    raise ValueError("Tipo de servico ativo nao encontrado.")
                prepared_items.append(
                    {
                        "tipo_servico_id": service_type["id"],
                        "tipo_servico_descricao": service_type["descricao"],
                        "data_servico": self._validate_service_date(item.get("data_servico")),
                        "os": str(item.get("os") or "").strip(),
                        "valor_centavos": value_cents,
                    }
                )
                total += value_cents

            seq = conn.execute(
                "UPDATE app_sequence SET value = value + 1 WHERE name = 'reembolso' RETURNING value"
            ).fetchone()
            number = f"{int(seq['value']):06d}"
            now = datetime.now().replace(microsecond=0)
            cur = conn.execute(
                """
                INSERT INTO reembolsos
                    (numero, motorista_id, motorista_nome, data_hora, valor_total_centavos)
                VALUES (?, ?, ?, ?, ?)
                """,
                (number, driver["id"], driver["nome"], now.isoformat(sep=" "), total),
            )
            reimbursement_id = int(cur.lastrowid)

            for item in prepared_items:
                conn.execute(
                    """
                    INSERT INTO reembolso_itens
                        (reembolso_id, tipo_servico_id, tipo_servico_descricao, data_servico, os, valor_centavos)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reimbursement_id,
                        item["tipo_servico_id"],
                        item["tipo_servico_descricao"],
                        item["data_servico"],
                        item["os"],
                        item["valor_centavos"],
                    ),
                )

        return self.get_reimbursement(reimbursement_id)

    def set_pdf_path(self, reimbursement_id: int, pdf_path: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE reembolsos SET pdf_path = ? WHERE id = ?",
                (pdf_path, reimbursement_id),
            )
            conn.commit()

    def get_reimbursement(self, reimbursement_id: int) -> dict:
        with get_connection() as conn:
            header = conn.execute(
                "SELECT * FROM reembolsos WHERE id = ?",
                (reimbursement_id,),
            ).fetchone()
            if not header:
                raise ValueError("Reembolso nao encontrado.")
            items = conn.execute(
                "SELECT * FROM reembolso_itens WHERE reembolso_id = ? ORDER BY id",
                (reimbursement_id,),
            ).fetchall()
        data = dict(header)
        data["items"] = [dict(row) for row in items]
        return data

    def list_history(
        self,
        search: str = "",
        start_date: str = "",
        end_date: str = "",
        service_type: str = "",
    ) -> list[dict]:
        where: list[str] = []
        params: list[str] = []
        if search.strip():
            like = f"%{search.strip()}%"
            where.append("(r.numero LIKE ? OR r.motorista_nome LIKE ?)")
            params.extend([like, like])
        if start_date:
            where.append("date(r.data_hora) >= date(?)")
            params.append(start_date)
        if end_date:
            where.append("date(r.data_hora) <= date(?)")
            params.append(end_date)
        if service_type.strip():
            where.append(
                "EXISTS (SELECT 1 FROM reembolso_itens ri2 WHERE ri2.reembolso_id = r.id AND ri2.tipo_servico_descricao = ?)"
            )
            params.append(service_type.strip())

        sql = """
            SELECT
                r.id,
                r.numero,
                r.data_hora,
                r.motorista_nome,
                r.valor_total_centavos,
                COUNT(ri.id) AS quantidade_itens
            FROM reembolsos r
            LEFT JOIN reembolso_itens ri ON ri.reembolso_id = r.id
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += """
            GROUP BY r.id
            ORDER BY r.data_hora DESC, r.id DESC
        """

        with get_connection() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    @staticmethod
    def _validate_service_date(value: str | None) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError("Todos os itens precisam de data.")
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("Data de serviço inválida.") from exc
        return text
