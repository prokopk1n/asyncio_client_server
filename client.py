import socket
import time


class ClientError(Exception):
	def __init__(self, description):
		self.description = description

	def __str__(self):
		return self.description + " here"


class Client:
	def __init__(self, host, port, timeout = None):
		addr = (host, port)
		self.socket = socket.create_connection(addr, timeout)

	def __del__(self):
		self.socket.close()

	def put(self, metric_name, value, timestamp = None):
		if timestamp is None:
			timestamp = int(time.time())

		try:
			self.socket.sendall(f"put {metric_name} {value} {timestamp}\n".encode("utf8"))
			serv_response = self.socket.recv(1024)
			if serv_response.decode("utf8") != "ok\n\n":
				raise Exception(serv_response.decode("utf8"))
		except Exception as e:
			raise(ClientError(str(e)))

	def get(self, metric_name):
		try:
			self.socket.sendall(f"get {metric_name}\n".encode("utf8"))
			full_response = ""

			while True:
				serv_response = self.socket.recv(1024)
				full_response += serv_response.decode("utf8")
				if serv_response.decode("utf8")[-1] == "\n" and serv_response.decode("utf8")[-2] == "\n":
					break

			if full_response[:3] != "ok\n":
				raise Exception(full_response)

			response = {}
			for data in full_response[3:].split("\n"):
				if not data:
					for key, value in response.items():
						value.sort(key=lambda x: x[0])
					return response

				data = data.split()
				if response.get(data[0]) is None:
					response[data[0]] = [(int(data[2]), float(data[1]))]
				else:
					response[data[0]].append((int(data[2]), float(data[1])))

		except Exception as e:
			raise(ClientError(str(e)))


if __name__ == "__main__":
	def test_get(full_response):
		try:
			if full_response == "error\nwrong command\n\n":
				raise Exception(full_response)

			response = {}
			for data in full_response[3:].split("\n"):
				if not data:
					return response

				data = data.split()
				if response.get(data[0]) is None:
					response[data[0]] = [(int(data[2]), float(data[1]))]
				else:
					response[data[0]].append((int(data[2]), float(data[1])))

		except Exception as e:
			raise (ClientError(str(e)))


	client = Client("localhost", 10001)
	print(client.get("*"))

	response = {'unsorted_data': [(1501865247, 13.045), (1501864247, 10.5), (1501864243, 11.0), (1501864248, 22.5)]}
	for key, value in response.items():
		value.sort(key=lambda x: x[1])
	print(response)