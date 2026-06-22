# 🧠 Casper HiveMind

> The first protocol where AI agents hire humans directly via HTTP 402 on Casper Network

## 🚨 The Problem

AI agents can't hire humans. They have no passport, no bank account, no Visa card. They can't register on Amazon Mechanical Turk or Toloka — those platforms require KYC.

**But they have a crypto wallet.**

Meanwhile, billions of Web2 users won't create crypto wallets just to earn small amounts on traditional platforms.

## 💡 The Solution

Casper HiveMind is a closed-loop Human-in-the-Loop economy built on Casper Network.

When an AI agent encounters a task it can't solve with confidence > 70%, it fires an **HTTP 402 Payment Required** request with a CSPR budget. A human receives the task in Telegram, answers with one tap, and gets paid instantly in CSPR — with zero gas fees.

**AI agents just got hands. Literally.**

## 🔄 How It Works
AI Agent confidence drops below 70%

↓

HTTP 402 Payment Required triggered

↓

Human receives task in Telegram

↓

One tap to answer

↓

Real CSPR transaction on Casper Testnet

↓

Live tx hash on cspr.live

## ⚡ Key Features

- **Account Abstraction** — wallet auto-created from Telegram ID, zero setup for users
- **Sponsored Transactions** — zero gas fees for humans, agent pays all costs
- **Reputation System** — 🥉 Beginner → 🥈 Verified → 🥇 Expert with 1.5x reward bonus
- **Honeypot Anti-Abuse** — hidden control tasks catch cheaters and protect quality
- **SQLite persistence** — balances and reputation survive server restarts
- **Real on-chain transactions** — every payment is a verified Casper Testnet deploy

## 🏗️ Tech Stack

- **Backend:** Python FastAPI + SQLite
- **Blockchain:** Casper Network (casper-client, Testnet)
- **Interface:** Telegram Bot API
- **Protocol:** HTTP 402 Payment Required

## 🚀 Roadmap

- [ ] CEP-78 NFT reputation passports on-chain
- [ ] Real AI agent integration (Claude/GPT API)
- [ ] External developer API for custom task submission  
- [ ] Referral system for viral growth
- [ ] Mainnet launch

## 🎯 Why Casper

- **Gas burning** — every microtransaction burns CSPR, fighting inflation automatically
- **Account Abstraction** — invisible wallets for Web2 users = true mass adoption
- **Upgradeable contracts** — reputation NFTs evolve without disruption
- **Sponsored Transactions** — agents pay gas, humans earn pure CSPR

## 📱 Demo

[Watch Demo Video](https://youtu.be/oNp2qIHISS4)

## 🔗 Live Bot

[@CasperHiveMind_bot](https://t.me/CasperHiveMind_bot)

## 👤 Built for

[Casper Agentic Buildathon 2026](https://dorahacks.io)