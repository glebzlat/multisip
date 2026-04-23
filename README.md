# MultiSIP

English [Russian](./README_ru.md)

SIP control application simplifying audio conference testing, built with
PySide6 and powered by BareSIP.

## Rationale

MultiSIP allows QA engineers to manually test audio conference functionality of
SIP clients without hussle. Until this project, QAs had to find physical SIP
phones, connect and setup them in order to register the required amount of
accounts for testing. This approach was messy, noisy, slow, and error-prone.

MultiSIP eliminates the problem, putting account control together into one
application. With MultiSIP QA engineers only need to start an instance,
register as many accounts as they need, and perform calls to these accounts.
MultiSIP accepts incoming calls and sets on hold automatically.

## Install

```bash
pip install .
```

## Run

```bash
multisip
```

## License

Licensed under [MIT License](./LICENSE).
