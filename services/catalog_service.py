from database.database import get_connection


class CatalogService:
    def list_drivers(self, include_inactive: bool = False) -> list[dict]:
        sql = "SELECT id, nome, ativo FROM motoristas"
        params: tuple = ()
        if not include_inactive:
            sql += " WHERE ativo = 1"
        sql += " ORDER BY nome COLLATE NOCASE"
        with get_connection() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def create_driver(self, name: str) -> int:
        name = self._clean_name(name)
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO motoristas (nome, ativo) VALUES (?, 1)",
                (name,),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_driver(self, driver_id: int, name: str, active: bool) -> None:
        name = self._clean_name(name)
        with get_connection() as conn:
            conn.execute(
                "UPDATE motoristas SET nome = ?, ativo = ? WHERE id = ?",
                (name, 1 if active else 0, driver_id),
            )
            conn.commit()

    def list_service_types(self, include_inactive: bool = False) -> list[dict]:
        sql = "SELECT id, descricao, ativo FROM tipos_servico"
        if not include_inactive:
            sql += " WHERE ativo = 1"
        sql += " ORDER BY descricao COLLATE NOCASE"
        with get_connection() as conn:
            return [dict(row) for row in conn.execute(sql).fetchall()]

    def create_service_type(self, description: str) -> int:
        description = self._clean_name(description).upper()
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO tipos_servico (descricao, ativo) VALUES (?, 1)",
                (description,),
            )
            conn.commit()
            return int(cur.lastrowid)

    def update_service_type(self, service_type_id: int, description: str, active: bool) -> None:
        description = self._clean_name(description).upper()
        with get_connection() as conn:
            conn.execute(
                "UPDATE tipos_servico SET descricao = ?, ativo = ? WHERE id = ?",
                (description, 1 if active else 0, service_type_id),
            )
            conn.commit()

    @staticmethod
    def _clean_name(value: str) -> str:
        clean = " ".join(str(value or "").strip().split())
        if not clean:
            raise ValueError("Informe uma descricao valida.")
        return clean
