def check_wrapper_config(wrapper_config_file):
    from aws_schema import SchemaValidator
    from os.path import dirname, realpath
    from json import load

    validation_file = f"{dirname(realpath(__file__))}/wrapper_config_schema.json"

    with open(wrapper_config_file, "r") as f:
        wrapper_config = load(f)

    SchemaValidator(file=validation_file).validate(wrapper_config)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "--wrapper-config-check",
        nargs="+",
        type=str,
        help="specify at least one configuration file to check the schema for",
    )
    args = parser.parse_args()

    for file in args.wrapper_config_check:
        check_wrapper_config(file)

    print("\n\t\tSUCCESS\n\tyour configurations are correct\n")
