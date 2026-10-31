"""Run a round notebook headless, from the top up to the review loop (section 12, which waits for typing).

    python3 tools/run_round.py notebooks/train_v5.ipynb

Executes the cells in the notebook's own kernel with notebooks/ as the working directory, prints each cell's text
output as it finishes, and writes the outputs back into the notebook (the review / fine-tune cells keep theirs).
Gold must already be checked: section 4 would otherwise wait for input. Stops at the first failing cell.
Reload the notebook from disk in Jupyter afterwards (File -> Reload Notebook from Disk -> Revert).
"""
import os, re, sys

import nbformat
from nbclient import NotebookClient

STOP = re.compile(r"^## 12\.")   # first heading of the review loop


def main(path):
    nb = nbformat.read(path, as_version=4)
    stop = next((k for k, c in enumerate(nb.cells) if c.cell_type == "markdown" and STOP.match(c.source)),
                len(nb.cells))
    run = nbformat.v4.new_notebook(cells=nb.cells[:stop], metadata=nb.metadata)

    def show(cell, cell_index, **_):
        if cell.cell_type != "code":
            return
        for o in cell.outputs:
            if o.output_type == "error":
                text = f"{o.ename}: {o.evalue}"
            else:
                text = o.get("text") or o.get("data", {}).get("text/plain", "")
            lines = [l for l in str(text).splitlines() if l.strip() and "%|" not in l]
            if lines:
                print(f"[cell {cell_index}]", *lines, sep="\n  ", flush=True)

    client = NotebookClient(run, timeout=None, resources={"metadata": {"path": os.path.dirname(os.path.abspath(path))}},
                            on_cell_executed=show)
    try:
        client.execute()
    finally:   # keep the outputs of whatever ran, even after a failure
        nb.cells[:stop] = run.cells
        nbformat.write(nb, path)
    print(f"ran sections up to the review loop ({stop} of {len(nb.cells)} cells), outputs saved to {path}")


if __name__ == "__main__":
    main(sys.argv[1])
