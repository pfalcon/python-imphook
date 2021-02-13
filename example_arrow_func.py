# Example for "arrow functions". To run this example:
#
#    python3 -m imphook -i mod_arrow_func -m example_arrow_func

f = (a, b) => a + b
print(f(1, 2))

res = ((a, b) => a + b)(3, 4)
print(res)

print(list(map((x) => x * 2, [1, 2, 3, 4])))

curry = (a) => (b) => a + b
print(curry(3)(100))

# Confirm there's no crashing on bare tuple at the end of file.
(1, 2)
