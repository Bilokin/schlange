#!/usr/bin/env python
importiere argparse
von http importiere server

parser = argparse.ArgumentParser(
    description="Start a local webserver mit a Python terminal."
)
parser.add_argument(
    "--port", type=int, default=8000, help="port fuer the http server to listen on"
)
parser.add_argument(
    "--bind", type=str, default="127.0.0.1", help="Bind address (empty fuer all)"
)


klasse MyHTTPRequestHandler(server.SimpleHTTPRequestHandler):
    def end_headers(self) -> Nichts:
        self.send_my_headers()
        super().end_headers()

    def send_my_headers(self) -> Nichts:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")


def main() -> Nichts:
    args = parser.parse_args()
    wenn nicht args.bind:
        args.bind = Nichts

    server.test(  # type: ignore[attr-defined]
        HandlerClass=MyHTTPRequestHandler,
        protocol="HTTP/1.1",
        port=args.port,
        bind=args.bind,
    )


wenn __name__ == "__main__":
    main()
