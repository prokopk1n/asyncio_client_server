import asyncio
import re
import json
import uuid


class HandleMetricsServer:

	def __init__(self, host, port, filename):
		self.host = host
		self.port = port
		self.regex_for_requests = re.compile(r"(get|put) ([a-zA-Z0-9.* ]+)\n")
		self.ok_message = "ok\n\n"
		self.error_message = "error\nwrong command\n\n"
		self.commands = {"put": self.put, "get": self.get}
		self.filename = filename

		file = open(filename, "w+")
		json.dump({}, file)
		file.close()

	def put(self, data):
		result = re.fullmatch(r"([^ ]+) ([0-9]+(?:\.[0-9]+)?) ([0-9]+)", data)
		if result is None:
			return self.error_message

		try:
			file = open(self.filename, "r+")
		except OSError:
			return self.error_message

		content = json.load(file)
		value = content.get(result.group(1), None)
		try:
			if value is None:
				content[result.group(1)] = {int(result.group(3)) : float(result.group(2))}
			else:
				value[int(result.group(3))] = float(result.group(2))

			file.seek(0)
			json.dump(content, file)
			file.close()
		except Exception as err:
			return self.error_message

		return self.ok_message

	def get(self, data):
		result = re.fullmatch(r"[^ ]+", data)
		if result is None:
			return self.error_message

		try:
			file = open(self.filename, "r+")
		except OSError:
			return self.error_message

		content = json.load(file)

		result_message = "ok\n"

		if data != "*":
			value = content.get(data, None)
			if value is not None:
				for timestamp, val in value.items():
					result_message += f"{data} {val} {timestamp}\n"
		else:
			for name, value in content.items():
				for timestamp, val in value.items():
					result_message += f"{name} {val} {timestamp}\n"

		file.close()
		return result_message + "\n"

	def process_data(self, request):
		result = self.regex_for_requests.fullmatch(request)
		if result is None:
			return self.error_message
		return self.commands[result.group(1)](result.group(2))

	async def handle(self, reader, writer):
		while True:
			try:
				request = await reader.readuntil(separator=b"\n")
			except asyncio.IncompleteReadError as err:
				writer.close()
				await writer.wait_closed()
				break

			writer.write(self.process_data(request.decode("utf8")).encode("utf8"))
			await writer.drain()

	async def main(self):
		server = await asyncio.start_server(self.handle, self.host, self.port)
		async with server:
			await server.serve_forever()


def run_server(host, port):
	asyncio.run(HandleMetricsServer(host, port, str(uuid.uuid4()) + ".json").main())


if __name__ == "__main__":
	run_server('localhost', 10001)
