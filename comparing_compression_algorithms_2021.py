from os import path, getcwd
from math import log, ceil
from collections import Counter

# .rle files
##########################
# first bit dictates if word-level compression was used (1) or not (0) - M
# second byte decides freq length in bits - F
# next F bits represent the frequency
# if M is 0
     # next ceil bits represent the character
# if M is 1
     # REPEAT
          # next ceil bits represent the character
     # UNTIL WORD_SEP signal found


# .ascii files
#########################
# each ceil bits represents a single ASCII character

# .huff files
#########################



WORD_SEP = 0x7f
ACCEPTED_FN_SPECIAL = [".", "_", "-"]
ACCEPTED_EXT = [".ascii", ".rle", ".huff"]
ASCII_LENGTH = 7


def decompress_rle(data):

     freq_or_val = 1                                   # expect frequency first

     mode = int(data[0])                               # if mode is 0 alternate frequency/value every chunk
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
          
          if freq_or_val:
               output += freq * run                   # end of last run
               run = ""                               # reset the run
               freq = int(chunk, 2)                   # get the new frequency
          else:
               delimiter = int(chunk, 2) == WORD_SEP  # check if chunk is a delimiter
               if delimiter:
                    run += " "
               else:
                    run += chr(int(chunk, 2))         # chunk must be a character

               
          if not mode or freq_or_val or delimiter:    # get ready for next frequency?             
               freq_or_val ^= 1

     output += freq * run
               
     print("output is")
     print(output)

          
               
class Node:
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


     
  

def compress_huff(data, word_level):
     print("Compressing text using huffman encoding.")

     node_list = [Node(freq_val[1], freq_val[0]) for freq_val in Counter(data).items()]

     # sort secondly by occurrence
     node_list = sorted(node_list, key=lambda n: data.index(n.value))
     
     # sort firstly from least to most used
     node_list = sorted(node_list)

     while len(node_list) > 1:                    # until we just have the root node left
          print(node_list)
          first = node_list.pop(0)                # take the two least-frequency nodes
          second = node_list.pop(0)
          parent = Node(first.freq + second.freq) # combine frequency to make a parent node
          parent.left = first
          parent.right = second
          node_list.append(parent)                # add parent back into list
          node_list = sorted(node_list)           # re-sort the node list
          

     root = node_list[0]
     char_map = {}
     char_map = traverse(root, char_map)

     print(char_map)


def traverse(tree, char_map, path="", depth=0):

     buffer = depth*"\t"

     if tree.value:
          print(buffer, "Found a leaf - path was", path)
          
          char_map[tree.value] = path
          path = ""

     
     print(depth*"\t", tree)

     depth += 1


     if tree.left is not None:
          print(buffer, "Connected on the left to...")
          lpath = path + "1"
          char_map = traverse(tree.left, char_map, lpath, depth)

     
     if tree.right is not None:
          print(buffer, "Connected on the right to...")
          rpath =  path + "0"
          char_map = traverse(tree.right, char_map, rpath, depth)

     return char_map

          
          

     

     

     
          
               
                    

               
               



def compress_rle(data, word_level):
     print("Compressing text using run length encoding.")

     
     freq_pairs = []
     count = 0
     last_chunk = None
     for chunk in data:
          chunk = list(chunk)

          if chunk != last_chunk and last_chunk is not None:
               if word_level:
                    last_chunk.append(WORD_SEP)
               freq_pairs.append([last_chunk, count])
               count = 1
          else:
               count += 1

          last_chunk = chunk

     freq_pairs.append([last_chunk, count])

     

     highest_freq = max(freq_pairs, key=lambda x: x[1])[1]
     highest_value = len(max(freq_pairs, key=lambda x: len(x[0])))

     print("The highest frequency was:", highest_freq)
     print("The highest value was:", highest_value)

     freq_bit_length = ceil(log(highest_freq, 2))
     

     output = [word_level, freq_bit_length]

     for pair in freq_pairs:

          value, freq = pair
          output.append(freq)
          for char in value:
               output.append(char)


     print(output)

     
     final = []
     for i, b in enumerate(output):
          if i == 0:
               fill = 1                 # first item of meta data is mode - single bit
          elif i == 1:
               fill = 8                 # second item decides freq bit length - one byte
          elif type(b) == str:
               fill = ASCII_LENGTH      # ASCII char values to use ceil bits each
               b = ord(b)
          else:
               fill = freq_bit_length   # frequency notation bits decided by max frequency

          final.append(bin(b)[2:].zfill(fill))

     print(final)

     return final
          
     

def save_raw_ascii(text):
     """Convert each character into a 7-bit 0-padded binary string"""
     return [bin(ord(char))[2:].zfill(ASCII_LENGTH) for char in text]

def load_raw_ascii(data):
     """Convert each 7-bit binary string into an ASCII character"""
     print("".join([chr(int(data[i:i+ASCII_LENGTH], 2)) for i in range(0, len(data), ASCII_LENGTH)]))


def write_binary(data, fn):
     with open(fn, "w") as f:
          for chunk in data:
               print(chunk, end="")
               f.write(chunk)

     print()

     size = path.getsize(getcwd()+"/"+fn)

     print(f"\nSaved file {fn}. Total size: {size} bytes.\n")
          
               


def valid_filename(fn, ext=False):
          
     for c in fn:
          if not any([c.isalpha(), c.isdigit(), c in ACCEPTED_FN_SPECIAL]):
               print("Sorry - please only include alphanumerical characters / valid symbols _ - . in your filename")
               return False

     if ext:
          if not any(fn.endswith(extension) for extension in ACCEPTED_EXT):
               print("Sorry, I can only load .ascii, .rle and .huff files.")
               return False
     elif path.exists(getcwd()+"/"+fn):
          x = input("File already exists, enter any key to overwrite: ")
          if x:
               return True
          else:
               return False
     
     return True

def valid_text(text):
     return all([ord(i) in range(0, 127) for i in text]) # don't allow final ASCII char (special use)

def compress():
     print("Enter text to compress...")

     text = input()
     while not valid_text(text):
          text = input("Enter ASCII characters only:\n")

     print("Enter filename to save under...")

     fn = input()
     while not valid_filename(fn):
          fn = input("Enter a valid filename:\n")
          
##
##     convert_funcs
##               
##     data = raw_ascii(data)

     x = input("""Enter 1 for character-level compression
Enter 2 for word-level compression""")

     word_level = 0
     if x == "2":
          raw_data = text.split(" ")
          word_level = 1
     else:
          raw_data = text

          
     compressed_data = compress_rle(raw_data, word_level)
     write_binary(compressed_data, fn+".rle")

     compressed_data = compress_huff(raw_data, word_level)
     write_binary(compressed_data, fn+".huff")

     ascii_data = save_raw_ascii(text)
     write_binary(ascii_data, fn+".ascii")
     #data = huffman(data)


def decompress():
     print("Enter filename to load from...")
     fn = input()
     while not valid_filename(fn, ext=True):
          fn = input("Enter a valid filename:\n")
          
     with open(fn) as f:
          data = f.read()

     if fn.endswith(".rle"):
          decompress_rle(data)
     elif fn.endswith(".ascii"):
          load_raw_ascii(data)

def main():

     x = input("""Enter 1 to enter text, compress, and save to file.
Enter 2 to load a file and decompress.""")

     if x == "1":
          compress()
     else:
          decompress()

if __name__ == "__main__":

     #main()
     compress_huff("pineapple", 0)
