# coincenter 🪙

A distributed asset trading system built for a Distributed Applications course. Users buy and sell fake crypto assets, managers create new ones, and everyone finds out about new listings the moment they're added, without polling anything.

The interesting part isn't the trading logic. It's that the notification layer runs on ZooKeeper instead of a database flag or a cron job, and every client-server call is TLS-encrypted from the start rather than bolted on later.

## Built for a Distributed Applications course (IT BSc). Graded 20 out of 20.

## Architecture

Three pieces talk to each other:

- **coincenter_flask.py**: the server. A Flask REST API backed by SQLite, running over TLS with a self-signed cert.
- **coincenter_data.py**: the data layer. All the SQL lives here, buying, selling, deposits, withdrawals, transaction history.
- **coincenter_client.py**: the client. A terminal menu that talks to the server over HTTPS and also opens a direct ZooKeeper connection to watch for new assets.

ZooKeeper sits alongside the REST API, not inside it. When a manager adds a new asset, the server writes a node under `/assets` in ZooKeeper. Every connected regular user has a `ChildrenWatch` on that path, so the moment the node changes, their client gets pushed a notification, no polling, no refresh button. Managers don't watch, since they're the ones causing the changes.

## Why ZooKeeper instead of something simpler

The obvious alternative is polling the API every few seconds to check for new assets. That works, but it means every idle client is making requests it almost never needs, and there's always a lag between something happening and a client finding out. A watch flips that: the client says once "tell me if this path changes" and then does nothing until ZooKeeper tells it something did. It's the same pattern real distributed systems use for config changes and service discovery, just applied here to "did a new coin get listed."

## Roles

Two kinds of users, same login flow. On first contact, the client asks the server if that user ID exists. If not, it asks whether the new account is a manager, then creates it.

- **Users** buy, sell, deposit, withdraw, and check their own balance.
- **Managers** do all of that plus create new assets, look up any user by ID, and pull transaction history for a date range.

There's no real authentication here, an ID plus a manager flag is the entire access model. That's a deliberate scope cut for a systems course project, not something to carry into anything real.

## Security bits worth mentioning

- All client-server traffic runs over HTTPS. The Flask app loads a certificate and key at startup and only serves TLS; the client pins the CA cert and verifies against it on every request instead of trusting whatever the OS ships.
- Money-moving operations (`buy`, `sell`, `deposit`, `withdraw`) check balance and supply server-side before touching the database. The client never decides whether a transaction is valid, it just asks and gets told yes or no.
- Every buy and sell writes a row to `Transactions`, so the ledger has a full history rather than just a current-state balance.

## What's not here

- No password, token, or session, just a user ID. Fine for a course exercise, not fine for anything with real money.
- The self-signed certificate and the SQLite file are intentionally left out of this repo. Spin up your own cert with `openssl` and run `setup_db.py` to get a fresh database with two seed users and two seed assets (BTC and ETH).

## Stack

Python, Flask, SQLite, ZooKeeper (via Kazoo), TLS/SSL, REST

## Context

Built for a Distributed Applications course (FCUL). The trading logic, ZooKeeper integration, and TLS setup are original work; the project brief and requirements come from the course.
