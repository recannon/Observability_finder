import argparse

def observability_finder():
    return


#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Check the observability of a list of solar system objects",
                                     epilog='Cannot accept limits in both airmass and elevation')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    return parser.parse_args()

def main():
    observability_finder()
    return


if __name__ == '__main__':
    main()
