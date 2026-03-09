CLIENT_ID = "1480247918207439011" 

STATUS = {

    "details": "Cheating with Passion",

    "large_image": "passionlogo",  
    "large_text": "getpassion.xyz",

    "small_image": "",
    "small_text": "",

    "buttons": [
        {"label": "🔥 Get Passion", "url": "https://getpassion.xyz/purchase"},
    ],

    "show_start_time": True,
}


def build_presence_kwargs(cfg: dict, start_time: float) -> dict:
    kwargs = {}

    if cfg.get("details"):
        kwargs["details"] = cfg["details"]
    if cfg.get("state"):
        kwargs["state"] = cfg["state"]
    if cfg.get("large_image"):
        kwargs["large_image"] = cfg["large_image"]
    if cfg.get("large_text"):
        kwargs["large_text"] = cfg["large_text"]
    if cfg.get("small_image"):
        kwargs["small_image"] = cfg["small_image"]
    if cfg.get("small_text"):
        kwargs["small_text"] = cfg["small_text"]
    if cfg.get("buttons"):
        kwargs["buttons"] = cfg["buttons"]
    if cfg.get("show_start_time"):
        kwargs["start"] = int(start_time)

    return kwargs


def rpcstatus():
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE":
        sys.exit(1)
    try:
        rpc = Presence(CLIENT_ID)
        rpc.connect()
    except Exception as e:
        sys.exit(1)

    start_time = time.time()
    kwargs = build_presence_kwargs(STATUS, start_time)
    rpc.update(**kwargs)

    try:
        while True:
            time.sleep(15) 
            rpc.update(**kwargs)
    except KeyboardInterrupt:
        rpc.clear()
        rpc.close()
