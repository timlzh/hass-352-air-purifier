class Response:
    ok: bool
    msg: str | None

    def __init__(self, resp: dict):
        self.ok = resp.get("success", False)
        self.msg = resp.get("errorMsg")

    def __str__(self) -> str:
        return f"{self.__dict__}"


class LoginByPwdResponse(Response):
    token: str | None

    def __init__(self, resp: dict):
        super().__init__(resp)
        self.token = resp.get("data", {}).get("token")
