from os import path, getcwd
from math import log, ceil
from collections import Counter
from timeit import default_timer

##############################################
######## comparing_compression_algorithms ####
##############################################
######### c.hall ######## 2021 ###############
##############################################

#########################
# .rle files
##########################
# first bit dictates if word-level compression was used (1) or character-level (0) - M
# the next byte decides freq length in bits - F
# next F bits represent the frequency
# if M is 0
#    next 7 bits represent the character
# if M is 1
#    REPEAT
#         next 7 bits represent the character
#    UNTIL EOW signal found

#########################
# .huff files
#########################
# first bit dictates if word-level compression was used (1) or character-level (0) - M
# the next byte represents how many bytes will be used to store the table length - X
# the next X bytes represent the length of the huffman table in bits

# next section represents the huffman table used - supports max frequency of 255.

# if M is 0
#    next 7 bits represent the character
#    next 8 bits represent the pattern length - P
#    next P bits represent the pattern used to encode the character

# if M is 1
#    REPEAT
#         next 7 bits represent the character
#    UNTIL EOW signal found

#    next 8 bits represent the pattern length - P
#    next P bits represent the pattern used to encode the word

# remaining bits represent the payload data

#########################
# .ascii files
#########################
# file comprised of 7 bit chunks
# each 7  bits represents a single ASCII character

##################################################

EOW = 0x7f
ACCEPTED_FN_SPECIAL = [".", "_", "-"]
ACCEPTED_EXT = [".ascii", ".rle", ".huff"]
ASCII_LENGTH = 7
TYPE_OR_LOAD = """Enter 1 to type in text
Enter 2 to load text from file
"""
COMPRESS_OR_DECOMPRESS = """Enter 1 to enter text, compress, and save to file.
Enter 2 to load a file and decompress.
"""
CHARACTER_OR_WORD = """Enter 1 for character-level compression
Enter 2 for word-level compression
"""

############################################

class MyTimer(object):
     """Timer object context manager to time process speed"""
     def __enter__(self):
          self.start = default_timer()
     def __exit__(self, type, value, traceback):
          self.end = default_timer()          
          print(f"That took {self.end-self.start} seconds.\n")

############################################

class Node:
     """Representation of a huffman tree node - sortable according to frequency"""
     def __init__(self, freq=0, value=None):
          self.left = None
          self.right = None
          self.freq = freq
          self.value = value

     def __repr__(self):
          return f"Frequency: {self.freq}   Value: {self.value}"

     def __lt__(self, other):
          if self.freq == other.freq:    # combined freq nodes take precedence
               if self.value is None:
                    return True
          
          return self.freq < other.freq

############################################
     
def binarise_huff_table(code_map, word_level):

     table = ""

     for value, encoding in code_map.items():
          if word_level == 0:
               char_code = bin(ord(value))[2:].zfill(ASCII_LENGTH)
               table += char_code                                          # character-mode...  represent ASCII character in 7 bits
               
          else:                                                       
               for char in value:                                          # in word-mode...
                    char_code = bin(ord(char))[2:].zfill(ASCII_LENGTH)
                    table += char_code                                     # each char is 7 bits
               table += bin(EOW)[2:]                                       # end with EOW marker.
          
          patt_length = bin(len(encoding))[2:].zfill(8)
          table += patt_length                                             # next byte stores the pattern length
          table += encoding                                                # next P bits stores the encoding pattern
     
     return table

############################################

def debinarise_huff_table(data, word_level):
     
     bit_lengths = [7, 8, None]
     current_chunk_type = 0
     code_map = {}
     value = ""
    
     while len(data):
          expected_bits = bit_lengths[current_chunk_type]                  # look at this many bits          
          chunk = data[:expected_bits]                 
          data = data[expected_bits:]                                      # remove from the bit stream
          chunk_as_char = chr(int(chunk, 2))

          if current_chunk_type == 0:
               if not word_level:
                    value = chunk_as_char                    
                    current_chunk_type = 1
               else:
                    if chunk_as_char == chr(EOW):                         
                         current_chunk_type = 1
                    else:
                         value += chunk_as_char

          elif current_chunk_type == 1:
               pattern_length = int(chunk, 2)
               bit_lengths[-1] = pattern_length
               current_chunk_type = 2

          else:
               code_map[chunk] = value + (" " if word_level else "")
               value = ""
               current_chunk_type = 0
               
     return code_map
          
############################################

def decompress_rle(data):
     print("Decompressing RLE data...")
    
     freq_or_val = 1                                   # expect frequency first

     word_level = int(data[0])                         # if mode is 0 alternate frequency/value every chunk
     freq_length = int(data[1:9], 2)                   # expect this many bits for each frequency

     data = data[9:]                                   # payload starts from here
     bit_lengths = [ASCII_LENGTH, freq_length]         # value bit length, frequency bit length

     output = ""
     freq = 0
     run = ""

     while len(data):
          expected_bits = bit_lengths[freq_or_val]     # look at this many bits
          chunk = data[:expected_bits]                 
          data = data[expected_bits:]                  # remove from the bit stream
          #print(chunk)
          
          if freq_or_val:
               output += freq * run                    # end of last run
               run = ""                                # reset the run
               freq = int(chunk, 2)                    # get the new frequency
          else:
               delimiter = int(chunk, 2) == EOW        # check if chunk is a delimiter
               if delimiter:
                    run += " "
               else:
                    run += chr(int(chunk, 2))          # chunk must be a character

               
          if not word_level or freq_or_val or delimiter:    # get ready for next frequency?             
               freq_or_val ^= 1

     if word_level:
          run += " "

     output += freq * run

     print(output)

############################################

def compress_huffman(data, word_level):
     print("Compressing text using huffman encoding.")

     node_list = [Node(freq_val[1], freq_val[0]) for freq_val in Counter(data).items()]

     # sort secondly by occurrence
     node_list = sorted(node_list, key=lambda n: data.index(n.value))
     
     # sort firstly from least to most used
     node_list = sorted(node_list)

     while len(node_list) > 1:                    # until we just have the root node left          
          first = node_list.pop(0)                # take the two least-frequency nodes
          second = node_list.pop(0)
          parent = Node(first.freq + second.freq) # combine frequency to make a parent node
          parent.left = first
          parent.right = second
          node_list.append(parent)                # add parent back into list
          node_list = sorted(node_list)           # re-sort the node list
          

     root = node_list[0]                          # start from the root node
     code_map = {}
     code_map = traverse_tree(root, code_map)     # and recursively traverse the tree to work out the encodings
     
     table_encoding = binarise_huff_table(code_map, word_level)     
     table_length_bits = bin(len(table_encoding))[2:]
     bytes_to_store_table_length = ceil(len(table_length_bits) / 8)
     table_length_bits = table_length_bits.zfill(bytes_to_store_table_length * 8)
     bytes_for_table_byte = bin(bytes_to_store_table_length)[2:].zfill(8)
     
     header = [str(word_level), bytes_for_table_byte, table_length_bits, table_encoding]
     payload = ["".join(code_map[item] for item in data)]

     return header + payload

############################################

def decompress_huffman(data):

     MODE = 0
     TL_BYTE_START = 1
     TABLE_LENGTH_START = 9     
     
     print("Decompressing huffman encoded data...")

     
     mode = int(data[0])
     table_length_bytes = int(data[TL_BYTE_START:TABLE_LENGTH_START], 2)
     table_length_end = TABLE_LENGTH_START+(table_length_bytes*8)
     table_length = int(data[TABLE_LENGTH_START:table_length_end], 2)    
     table_start = table_length_end
     table_end = table_length_end + table_length     
     table = data[table_start:table_end]     
     payload = data[table_end:]
     
     code_map = debinarise_huff_table(table, mode)

     value = ""
     output = ""

     for bit in payload:
          value += bit
          if value in code_map:
               output += code_map[value]
               value = ""
          
     print(output)

############################################

def traverse_tree(tree, code_map, path="", depth=0):

     buffer = depth*"\t"

     if tree.value:
          #print(buffer, "Found a leaf - path was", path)          
          code_map[tree.value] = path
          path = ""
     
     #print(depth*"\t", tree)
     depth += 1

     if tree.left is not None:
          #print(buffer, "Connected on the left to...")
          lpath = path + "1"
          char_map = traverse_tree(tree.left, code_map, lpath, depth)
     
     if tree.right is not None:
          #print(buffer, "Connected on the right to...")
          rpath =  path + "0"
          char_map = traverse_tree(tree.right, code_map, rpath, depth)

     return code_map

############################################

def compress_rle(data, word_level):
     print("Compressing text using run length encoding.")
          
     freq_pairs = []
     count = 0
     last_chunk = None
     for chunk in data:
          chunk = list(chunk)

          if chunk != last_chunk and last_chunk is not None:
               if word_level:
                    last_chunk.append(EOW)
               freq_pairs.append([last_chunk, count])
               

               count = 1
          else:
               count += 1

          last_chunk = chunk

     freq_pairs.append([last_chunk, count])

     highest_freq = max(freq_pairs, key=lambda x: x[1])[1]
     highest_value = len(max(freq_pairs, key=lambda x: len(x[0])))

     #print("The highest frequency was:", highest_freq)
     #print("The highest value was:", highest_value)

     freq_bit_length = len(bin(highest_freq)[2:])
     

     output = [word_level, freq_bit_length]

     for pair in freq_pairs:

          value, freq = pair
          output.append(freq)
          for char in value:
               output.append(char)
     
     final = []
     for i, b in enumerate(output):
          if i == 0:
               fill = 1                 # first item of meta data is mode - single bit
          elif i == 1:
               fill = 8                 # second item decides freq bit length - one byte
          elif type(b) == str:
               fill = ASCII_LENGTH      # ASCII char values to use 7 bits each
               b = ord(b)
          else:
               fill = freq_bit_length   # frequency notation bits decided by max frequency

          final.append(bin(b)[2:].zfill(fill))

     return final
          
############################################    

def save_raw_ascii(text):
     """Convert each character into a 7-bit 0-padded binary string"""
     print("Saving raw uncompressed ASCII...")
     return [bin(ord(char))[2:].zfill(ASCII_LENGTH) for char in text]

############################################

def load_raw_ascii(data):
     """Convert each 7-bit binary string into an ASCII character"""
     print("".join([chr(int(data[i:i+ASCII_LENGTH], 2)) for i in range(0, len(data), ASCII_LENGTH)]))

############################################

def write_binary(data, fn):
     with open(fn, "w") as f:
          for chunk in data:
               f.write(chunk)

     print()
     size = path.getsize(getcwd()+"/"+fn)
     print(f"Saved file {fn} - total size: {size} bytes.\n")         

############################################

def validate_filename(fn, ext=None):
          
     for c in fn:
          if not any([c.isalpha(), c.isdigit(), c in ACCEPTED_FN_SPECIAL]):
               print("Sorry - please only include alphanumerical characters / valid symbols _ - . in your filename")
               return False

     if ext:
          if not any(fn.endswith(extension) for extension in ext):
               print("Sorry, I can only load {} files.".format(", ".join(ext)))
               return False
     elif path.exists(getcwd()+"/"+fn):
          x = input("File already exists, enter any key to overwrite: ")
          if x:
               return True
          else:
               return False
     
     return True

############################################

def sanitise_text(text):
     sanitised = "".join([t for t in text if ord(t) in range(0, 127)])
     if text != sanitised:
          print("Non ASCII chars detected - I have removed these from your data.")
     return sanitised


############################################

def get_text_from_console():
     print("Enter text to compress...")
     text = input()
     return sanitise_text(text)

############################################

def get_text_from_file():
     print("Enter filename to load from...")
          
     fn_valid = False
     text_valid = False
     while not (fn_valid):               
          fn = input("Enter a valid filename:\n")
               
          fn_valid = validate_filename(fn, ext=[".txt"])
          if not fn_valid:
               continue
          
          with open(fn) as f:
               text = f.read()
               
          text = sanitise_text(text)
          
     return text

############################################

def compress():
     choice = input(TYPE_OR_LOAD)
     if choice == "1":
          text = get_text_from_console()
     else:
          text = get_text_from_file()
          

     print("Enter filename to save under...")
     fn = input()
     while not validate_filename(fn):
          fn = input("Enter a valid filename:\n")

     choice = input(CHARACTER_OR_WORD)

     word_level = 0
     if choice == "2":
          raw_data = [i for i in text.strip().split(" ") if i != ""]
          word_level = 1
     else:
          raw_data = text.strip()

     with MyTimer() as t:
          compressed_data = compress_rle(raw_data, word_level)
          write_binary(compressed_data, fn+".rle")
     
     with MyTimer() as t:
          compressed_data = compress_huffman(raw_data, word_level)
          write_binary(compressed_data, fn+".huff")
     
     with MyTimer() as t:
          ascii_data = save_raw_ascii(text)
          write_binary(ascii_data, fn+".ascii")

############################################
     
def decompress():
     print("Enter filename to load from...")
     fn = input()
     while not validate_filename(fn, ext=ACCEPTED_EXT):
          fn = input("Enter a valid filename:\n")
          
     with open(fn) as f:
          data = f.read()

     if fn.endswith(".rle"):
          with MyTimer() as t:
               decompress_rle(data)
               
     elif fn.endswith(".ascii"):
          with MyTimer() as t:   
               load_raw_ascii(data)
               
     else:
          with MyTimer() as t:               
               decompress_huffman(data)

############################################
     
def main():
     choice = input(COMPRESS_OR_DECOMPRESS)
     if choice == "1":
          compress()
     else:
          decompress()

############################################

if __name__ == "__main__":
     
     while True:
          main()

