import base64
import hashlib
from typing import Any, cast

from cryptography.hazmat.primitives.asymmetric import (
    padding,
    rsa,
)
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import load_der_private_key


class SignUtil:
    # 逆向得到的私钥串填入下方
    HEX_PRIVATE_KEY = "308204BD020100300D06092A864886F70D0101010500048204A7308204A30201000282010100A58E740A4CDA7A959DBD2574D8BC970436B24D898C81694F630B46EB7022B89D0756BD06708A639287E675DF42D7B0C6B693EB314D33028A5A4556D00B39CFA005C97D010C7B6584F9D7101596DA9D53D7527D553CB2B889BBBE8FFF65817752324EF67C85B5C555DD30ABC8B8609D7388FF084838FF0D3B24CD2CD5A30D6BE4E94247AF882CA9E49E2F41DBA5CF5467C7CA56039F2CEEA86F3EFF2C8DEB9FCA6FFEE625E9E92A3E51ABB35C2B0D25259A11526BF9F89D67AB19A425694DF1A308DAD39949EAE3B8EE2954DAD928BF1CD8F88827B922BC2F590FA22E139F89FFE7384EC896737D5C45B58A2078525E46E96FA02FB69BD0F1648E0EE726AC1D3F02030100010282010011A9B117A83B66F8AF6B8EA378BC26207CF568F053DD3AAF0D92166EE7F7CC5A747DFC8CC355006A91B534BE2D1375F8BD61EAA5C7E6B94EA972DC6035D265245D79B1AC7AF86F4C509B714BDC5C568CAB5C51A2D666FAE936EE8DCE61B5FE54F6A916031300E19CD78C69C770645E680525B06C842831F12D6BF66C9488CA09E5565B3B8B5702B7060556B28E875C0FA8E60A3ABEF721716F6F29A390711CBBA5DA818C7DB64013ECF411556C1B0EE556FF3ED8A347F44804C484E1EBA39FE09F695028479E020F639CA3B68F590BADD69C080270108A790E29B8AA209750014D871B3415EAA3905183AECC0DA007EEA0438DEFD5A357865AEA8B446909348102818100FA0682B9F4C095B686B29FA4EAAE87D3D79E64B69CB1282D5A820FDA3035F85D2B7B103BB930C4B3DC6C12720BC6DEE09CE4078CAA2C6B99B8113CA4FEC9AE0F26D8BEF565D0D3AC57069F29FA7BB9A98DD1B5512F7A2116D363D4404775E4C611D95FCC4EC10756D0901CD51F470968A363BD16FEB3A92C3FDE05750BE44E9502818100A98337B57B4F71FB645C88BC1AD6995AEECA954CAC4CE537183B235BF4AD8E5B0343B606561CA6C77DBE3A0CC7629395078DBCD12CA0914AFB5C686FFE862F8129B30301EC12ADBA5E750A843C6B97A6C2E1BF8FF1D2FBFD423376807F5E58C13F1850FDFF1A6375BF65DAD9D4CB4645A98E00D951DBF50902177FD16F398B83028180291D52F7F3588C0604E670BC34DF5874AC9B5E626D27F0BC6C8AC0C29774F88F91ABDE02843491D425E61BAE67635F993E137D6E533994C42571A83055B9A286D953812B677FCC9F257C7045FDEBC49F2E341305F3B1B8A9413FC45281ADD05E05E7620A7DD4DE391778EB54DC9CD8DE3D28149B286D30DF96ED12A6A9BAF4750281800F6DB70B589EE183FD1D830083FCD656757790E13AA9810F63B03646AF5D80A07E0A92ADBEF6BAA35BA98DC50DFCC5EC0195000395E943702CB2BB7ABE12DE8E060A9A1279B73582CA08231DE815EEE6A9C43C5850AD606C2BB35D6CD2AAF6AF181C117B1CD5FD09819336B92EEA158A4FA5722455940C98764D473FFBBCA41B02818100D01BEF75BE36309F689F889E2747B8F717584E16C9B9E9D213FBFDCEB3E886C1AE298563F4608EBE9AD9B69D47D2571D94B7256CE62EF516ABC53C117ED305EAD4657E4C58CBAC72E4FE1D8FC09AD959B6A7A82E205AA5B61E3DBF7509BB88A687ABAE8021ACD5D0C617C4DDAF97ED0F7AB7BCA20258B06B37E74B11FE15084F"

    @classmethod
    def load_private_key(
        cls,
    ) -> rsa.RSAPrivateKey:
        """
        从十六进制字符串加载 DER 格式的 PKCS#8 私钥
        """
        der = bytes.fromhex(cls.HEX_PRIVATE_KEY)
        # 无密码
        return cast(rsa.RSAPrivateKey, load_der_private_key(der, password=None))

    @classmethod
    def __to_string(cls, value: Any):
        """
        将值转换为字符串
        """
        if isinstance(value, str):
            return value
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode("utf-8")

        return str(value)

    @classmethod
    def build_query_string(cls, params: dict) -> str:
        """
        对字典按 key 升序拼接：key1=value1&key2=value2...
        """
        items = sorted(params.items(), key=lambda x: x[0])
        return "&".join(f"{k}={cls.__to_string(v)}" for k, v in items)

    @classmethod
    def sign_params(cls, params: dict) -> str:
        """
        给定参数 dict，返回 Base64(URL-safe) 编码的 SHA1withRSA 签名字符串（无换行）
        """
        private_key = cls.load_private_key()
        query = cls.build_query_string(params).encode("utf-8")
        # 签名
        signature = private_key.sign(query, padding.PKCS1v15(), SHA1())
        # Base64 编码并去除换行
        return base64.b64encode(signature).decode("utf-8").replace("\n", "")

    @classmethod
    def hash_md5(cls, s: str) -> str:
        try:
            md5 = hashlib.md5()
            md5.update(s.encode())
            digest = md5.digest()

            result = ""
            for byte in digest:
                val = byte
                if val < 16:
                    result += "0"
                result += format(val, "x")
            return result.upper()
        except Exception as e:
            print(e)
            return ""

    @classmethod
    def checksum(cls, payload: bytes) -> int:
        """
        计算校验和，返回原数据和校验和
        """
        checksum = 0
        for b in payload:
            checksum += b
            checksum = checksum & 0xFF

        return checksum

    @classmethod
    def with_checksum(cls, payload: bytes) -> bytes:
        return payload + bytearray([cls.checksum(payload)])


# 示例用法
if __name__ == "__main__":
    data = {"token": "test"}
    print(sign := SignUtil.sign_params(data))  # 打印签名字符串
