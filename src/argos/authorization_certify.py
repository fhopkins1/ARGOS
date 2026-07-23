"""Command entrypoint for package-bound Authorizations certification."""

from .authorization_package_certification import main


if __name__ == "__main__":
    raise SystemExit(main())
