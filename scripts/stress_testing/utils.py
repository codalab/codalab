from subprocess import check_output


def run_shell_script(script, print_output=False):
    if '"' in script:
        assert Exception("Docker shell script cannot contain double quotes, turn it into a single quote!")

    output = check_output([
        "docker",
        "exec",
        "-it",
        "django",
        "bash",
        "-c",
        'echo "{}" | python manage.py shell_plus'.format(script)
    ])

    if print_output:
        print(output)

    return output
