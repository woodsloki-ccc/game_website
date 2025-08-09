import asyncio
import json
import time
from websockets import serve, Response, Headers
import csv

port = 60000

class Vector3f:
    def __init__(self, x, y, z) -> None:
        self.x = x
        self.y = y
        self.z = z

class Player:
    def __init__(self) -> None:
        self.pos = Vector3f(0, 0, 0)

login_page = ""
game_page = ""

with open("game_page.html", "r") as f:
    for line in f.readlines():
        game_page += line

with open("login_page.html", "r") as f:
    for line in f.readlines():
        login_page += line

async def process_request(server, request):
    if request.path == "/ws":
        return None
    
    elif request.path == "/login/ws":
        return None
    
    elif request.path == "/game/ws":
        return None
    
    elif request.path == "/login":
        body = login_page.encode("utf-8")
        headers = Headers([
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Connection", "Update"),
        ])
        return Response(200, "OK", headers, body)
    
    elif request.path == "/game":
        body = game_page.encode("utf-8")
        headers = Headers([
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Connection", "Update"),
        ])
        return Response(200, "OK", headers, body)
    
    else:
        body = "<html><html/>".encode("utf-8")
        headers = Headers([
        ])
        return Response(200, "OK", headers, body)
    
connected = set()

accounts_in_game = []
players_in_game  = []

accounts = { #["username", "password", authcode, last responce]
    1 : ["admin", "password" , 0, 0],
    2 : ["admin2", "password", 0, 0]
}

player_data = { #storeage
    1 : Player(),
    2 : Player()
}

async def handle_login(websocket, data):
    username = data.get("username")
    password = data.get("password")

    for account in accounts:
        if username == accounts[account][0]:
            accounts[account][3] = int(time.time()*1000)
            if password == accounts[account][1]:
                if accounts[account][2] == 0:
                    authToken = 5
                    await websocket.send(json.dumps(
                        {
                            "type"      : "login",
                            "subtype"   : "return data",
                            "username"  : username,
                            "account_id": account,
                            "success"   : True,
                            "authToken" : authToken
                        }
                    ))
                    accounts[account][2] = authToken
                    accounts_in_game.append(account)
                    players_in_game.append(player_data[account])
            else:
                await websocket.send(json.dumps(
                    {
                        "type"     : "login",
                        "subtype"  : "return data",
                        "username" : username,
                        "success"  : False,
                        "authToken": 0
                    }
                ))

async def handle_game(websocket, data):
    try:
        account_id = int(data.get("account_id"))
    except TypeError:
        print("invalid id:", data.get("account_id"))
        await websocket.send(json.dumps(
            {
                "type"     : "game",
                "subtype"  : "change site",
                "site"     : "/login"
            }
        ))
        return
    
    username   = data.get("username")
    authToken  = data.get("authToken")
    in_game = False
    for acccount in accounts_in_game:
        if account_id == acccount:
            in_game = True

    if in_game == False:
        await websocket.send(json.dumps(
            {
                "type"     : "game",
                "subtype"  : "change site",
                "site"     : "/login"
            }
        ))
        return

    accounts[account_id][3] = int(time.time()*1000)
    if accounts[account_id][0] == username and accounts[account_id][2] == authToken:
        players_data = {}
        for player_id in accounts_in_game:
            if player_id != account_id:
                players_data[player_id]["x"] = player_data[player_id].pos.x
                players_data[player_id]["y"] = player_data[player_id].pos.y
                players_data[player_id]["z"] = player_data[player_id].pos.z

        await websocket.send(json.dumps(
            {
                "type"     : "game",
                "subtype"  : "update data",
                "players"  : {}
            }
        ))   

async def websocket_handler(websocket):
    connected.add(websocket)
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                with open("log.txt", "a") as f:
                    f.write(str(data) + "\n")
                msg_type = data.get("type")

                if msg_type == "login":
                    await handle_login(websocket, data)
                elif msg_type == "game":
                    await handle_game(websocket, data)
                else:
                    await websocket.send(json.dumps({"error": "Unknown message type"}))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON"}))
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected.remove(websocket)

async def main():
    print(f"Serving on http://localhost:{port}/ and ws://localhost:{port}/ws")

    asyncio.create_task(game_update())

    async with serve(
        websocket_handler,
        "localhost",
        port,
        process_request=process_request,
    ):
        await asyncio.Future()  # Run forever

async def game_update():
    while True:
        await asyncio.sleep(1)

        c_time = int(time.time()*1000)

        for account in accounts_in_game:
            print(account, c_time - accounts[account][3])
            if c_time - accounts[account][3] > (10 * 1000): 
                try:
                    accounts_in_game.remove(account)
                    accounts[account][2] = 0 #resets auth code so you can relog
                except ValueError:
                    pass
        miniLog = "####\n"

        for account in accounts_in_game:
            miniLog += f"{accounts[account][1]} is still in game\n"
        miniLog += "####\n"
        
        print(f"\033c{miniLog}")
                

if __name__ == "__main__":
    asyncio.run(main())
