"""Astra-grown placeholder tool: echo a message. Used to prove the tool-invocation path."""
import sys
if len(sys.argv) > 1:
    print(" ".join(sys.argv[1:]))
else:
    print("Astra is here. Say something after the command.")
