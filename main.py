from indexer import Indexer
from querier import Querier
from interface import Interface


if __name__ == "__main__":
    indexer = Indexer()
    indexer.start_indexing()

    querier = Querier()

    # Determine the display mode for the search engine
    display_mode = None
    while display_mode not in ("C", "G"):
        display_mode = input("Enter \'C\' for console mode or \'G\' for GUI mode: ").upper()
        print()

    if display_mode == "C":
        querier.run_console()
    else:
        interface = Interface(querier)


