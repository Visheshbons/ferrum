# Ferrum (Worldbuilder Instructions)

> [!IMPORTANT]
> PLEASE NOTE that this game is still in a very early stage.
> Be patient, but report any bugs or issues.

## Installation

All installation instructions can be found under the [Playtester instructions](./PLAYTESTERS.md).

## Running the Game
Once you have installed python, and now are in the game folder, you can run the game for testing.

You can use the command line, with
```bash
python main.py
```
Make sure you run this from the directory of the game you are in.
For example:

This is WRONG, and throws an error.
```bash
vishesh@fedora:~$ python main.py
python: can't open file '/home/vishesh/main.py': [Errno 2] No such file or directory
vishesh@fedora:~$ 
```

This is CORRECT, and runs correctly.
```bash
vishesh@fedora:~/Desktop/Code/Ferrum$ python main.py
Hello from the pygame community. https://www.pygame.org/contribute.html
vishesh@fedora:~/Desktop/Code/Ferrum$ 
```

To edit a world, you can use the following command:
```bash
python main.py --edit levels/lv1.world
```
This edits level 1.
All other levels can be accessed in the same way.