
from algorithms.crc import CRC
from algorithms.hamming import Hamming
from algorithms.parity import Parity

class EncoderDecoder:
    def __init__(self):
        self.parity = Parity()
        self.crc = CRC()
        self.hamming = Hamming()

    def encode_binary_string(self, msg) -> list[str]:
        return [format(ord(x), 'b') for x in msg]

    def decode_data_parity(self, data):
        ans = self.parity.has_odd_parity(data)
        
        has_error = ans
        return has_error

    def decode_data_crc(self, data):
        key = "1001"
        ans = []
        
        for i in range(len(data)//10):
            ans.append(self.crc.decode_data(data[i*10:(i+1)*10], key))

        print("Remainder after decoding is-> ", ans)
        # If remainder is all zeros then no error occurred
        temp = "0" * (len(key) - 1)

        has_error = False
        for i in range(len(ans)):
            if ans[i] != temp:
                has_error = True
        return has_error

    def decode_data_hamming(self, data):
        ans = []
        
        for i in range(len(data)//11):
            ans.append(self.hamming.decode_data(data[i*11:(i+1)*11]))
        
        has_error = any(ans)
        return has_error
    
    def encode_data_parity(self, data):
        return self.parity.encode_odd_data(data)

    def encode_data_crc(self, data):
        key = "1001"
        return self.crc.encode_data(data, key)

    def encode_data_hamming(self, data):
        return self.hamming.encode_data(data)