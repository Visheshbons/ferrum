# Ferrum (Playtester Instructions)

> [!IMPORTANT]
> PLEASE NOTE that this game is still in a very early stage.
> Be patient, but report any bugs or issues.

## Installation

### Python
If you already have python installed with a decently recent version, you can skip this step.

#### Linux
Most Linux distros already have python installed.
You can check your version using:
```bash
python --version
```
You should see something like this if python is installed:
```bash
vishesh@fedora:~$ python --version
Python 3.14.5
vishesh@fedora:~$ 
```

For Debain-based systems with APT as the package manager, run
```bash
sudo apt install python3
```

For Red Hat based systems with the DNF package manager, run
```bash
sudo dnf install python3.14
```

If you encounter any issues, look through your distro's documentation on Python.

The developers of the game use python 3.14.5, which can be checked via
```bash
python --version
```

#### Windows
Installing Python on Windows is relatively straightforward.

You can either go through the command line with
```powershell
winget install Python.Python.3.14
```
Or, you can install python via [Python's official site](https://www.python.org/), where you can follow the basic installation instructions.

The developers of the game use python 3.14.5, which can be checked via
```powershell
python --version
```

#### MacOS
MacOS often comes with Python pre-installed. You can check via:
```zsh
python --version
```
You should see something like
```zsh
$ python --version
Python 3.14.5
```
If not, you can install python with 
```zsh
brew install python
```
Or, if you are uncomfortable with using the command line, feel free to go to [Python's official site](https://www.python.org/), where you can follow the instructions provided.

### Installing the Game
Once you have python installed, you can start installing the game.

> [!TIP]
> If you are actively using Git in your system, simply run
> ```bash
> git clone https://github.com/Visheshbons/ferrum.git
> ```
> Then skip to [Running the Game](#running-the-game)

Go to the [root directory](https://github.com/Visheshbons/ferrum) of this project on Github.

Then, under "Code", click "Download ZIP".
Once the ZIP file has been downloaded, extract the folder from the ZIP.

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
