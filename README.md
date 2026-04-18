# Screaming-side-channel

## Basic usage

1. Setup:
```
# as root: ./scripts/env_setup_root.sh
./scripts/env_setup.sh
```
1. Run Jupyter notebook: `./scripts/run_jupyter.sh`
1. Get chipwhisperer python environment: `source ./scripts/env.sh`

## Project structure
- `script` - general setup and environment scripts
- `env` - target directory of setup step (chipwhisperer repository and python virtual environment)
- `firmware` - source code for target firmware
- `software` - everything running on the computer for (managing probing, processing and communicating with the target)
- `testing` - support for checking that things work

## Workflow for sharppeak capturing system(draft system) - in `software/collect_sharppeak`

* `collect_sharppeak.py` is the Python flowgraph generated from the GNU Radio `.grc` file.
* `run_collect_sharppeak.py` is used to control `collect_sharppeak.py`.

### How it works

* `run_collect_sharppeak.py` starts the GNU Radio flowgraph and keeps it running.
* By default, GNU Radio does **not** save data.
* `run_collect_sharppeak.py` listens on a local port.
* The origin ChipWhisperer capture script is modified to send trigger commands to this port before each AES encryption.


For each AES execution:

* before the AES operation starts, the ChipWhisperer script sends a **start** signal to `run_collect_sharppeak.py`
* GNU Radio then starts writing data to file
* after a short delay(currently it is a guessed value, it should cover all AES encryption), the ChipWhisperer script sends a **stop** signal
* GNU Radio stops saving


* `"1"` means start saving
* `"0"` means stop saving

### Running order

1. Run `run_collect_sharppeak.py`
2. Run the ChipWhisperer capture script
3. During each AES trace, the ChipWhisperer script triggers GNU Radio to start and stop saving

