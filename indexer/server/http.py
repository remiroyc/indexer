from aiohttp import web
import aiohttp_cors

from pymongo.database import Database


class WebServer:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def addr_to_ids(self, request):
        try:
            addr = request.rel_url.query["addr"]
            documents = self.database["starknet_ids"].find(
                {"owner": addr, "_chain.valid_to": None}
            )
            return web.json_response(
                {"ids": [document["token_id"] for document in documents]}
            )
        except Exception:
            return web.json_response({"ids": []})

    async def field_data_to_id(self, request):
        try:
            field = request.rel_url.query["field"]
            data = request.rel_url.query["data"]
            verifier = request.rel_url.query["verifier"]
            document = self.database["starknet_ids_data"].find_one(
                {
                    "field": field,
                    "data": data,
                    "verifier": verifier,
                    "_chain.valid_to": None,
                }
            )
            return web.json_response({"id": document["token_id"]})
        except Exception:
            return web.json_response({"error": "no token found"})

    async def tokenid_to_domain(self, request):
        try:
            token_id = request.rel_url.query["id"]
            document = self.database["domains"].find_one(
                {
                    "token_id": token_id,
                    "_chain.valid_to": None,
                }
            )
            return web.json_response({"domain": document["domain"]})
        except Exception:
            return web.json_response({"error": "no domain found"})

    async def domain_to_addr(self, request):
        try:
            domain = request.rel_url.query["domain"]
            document = self.database["domains"].find_one(
                {
                    "domain": domain,
                    "_chain.valid_to": None,
                }
            )
            return web.json_response({"addr": document["addr"]})
        except Exception:
            return web.json_response({"error": "no address found"})

    async def addr_to_domain(self, request):
        try:
            addr = request.rel_url.query["addr"]
            document = self.database["domains"].find_one(
                {
                    "rev_addr": addr,
                    "_chain.valid_to": None,
                }
            )
            return web.json_response({"domain": document["domain"]})
        except Exception:
            return web.json_response({"error": "no domain found"})

    async def addr_to_available_ids(self, request):
        try:
            addr = request.rel_url.query["addr"]

            documents = self.database["starknet_ids"].find(
                {"owner": addr, "_chain.valid_to": None}
            )
            ids = [document["token_id"] for document in documents]
            available = []
            for token_id in ids:
                found = self.database["domains"].find_one(
                    {"token_id": token_id, "_chain.valid_to": None}
                )
                print("found:", found)

            return web.json_response({"ids": available})
        except Exception:
            return web.json_response({"ids": []})

    async def addr_to_domains(self, request):
        try:
            addr = request.rel_url.query["addr"]
            ids = self.owners_db[addr]
            domains = []
            for sid in ids:
                try:
                    document = self.database["domains"].find_one(
                        {
                            "token_id": sid,
                            "_chain.valid_to": None,
                        }
                    )
                    if document:
                        domains.append(document["domain"])
                except KeyError:
                    pass
            return web.json_response({"domains": domains})
        except Exception:
            return web.json_response({"domains": []})

    async def uri(self, request):
        try:
            id = request.rel_url.query["id"]
            document = self.database["domains"].find_one(
                {
                    "token_id": id,
                    "_chain.valid_to": None,
                }
            )
            if document:
                domain = str(document["domain"])
                return web.json_response(
                    {
                        "name": domain,
                        "description": "This token represents an identity on StarkNet that can be linked to external services.",
                        "image": f"https://starknet.id/api/identicons/{id}",
                    }
                )
            else:
                return web.json_response(
                    {
                        "name": f"Starknet ID: {id}",
                        "description": "This token represents an identity on StarkNet that can be linked to external services.",
                        "image": f"https://starknet.id/api/identicons/{id}",
                    }
                )
        except Exception:
            return web.json_response({"error": "no id specified"})

    def build_app(self):
        app = web.Application()
        app.add_routes([web.get("/addr_to_ids", self.addr_to_ids)])
        app.add_routes([web.get("/addr_to_available_ids", self.addr_to_available_ids)])
        app.add_routes([web.get("/field_data_to_id", self.field_data_to_id)])
        app.add_routes([web.get("/uri", self.uri)])
        app.add_routes([web.get("/tokenid_to_domain", self.tokenid_to_domain)])
        app.add_routes([web.get("/domain_to_addr", self.domain_to_addr)])
        app.add_routes([web.get("/addr_to_domain", self.addr_to_domain)])
        app.add_routes([web.get("/addr_to_domains", self.addr_to_domains)])

        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            },
        )
        for route in list(app.router.routes()):
            cors.add(route)
        return app
