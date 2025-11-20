-- Cryptocurrency Database - Seed Data
-- Comprehensive test data for crypto trading platform
-- Includes realistic OHLCV data, user holdings, transactions, and more

-- =====================================================
-- 1. BLOCKCHAINS
-- =====================================================

INSERT INTO blockchains (name, symbol, chain_id, consensus_mechanism, block_time_seconds, native_token, status, launched_date) VALUES
('Ethereum', 'ETH', 1, 'PoS', 12, 'ETH', 'active', '2015-07-30'),
('Bitcoin', 'BTC', NULL, 'PoW', 600, 'BTC', 'active', '2009-01-03'),
('Binance Smart Chain', 'BSC', 56, 'PoSA', 3, 'BNB', 'active', '2020-09-01'),
('Solana', 'SOL', NULL, 'PoH', 1, 'SOL', 'active', '2020-03-16'),
('Polygon', 'MATIC', 137, 'PoS', 2, 'MATIC', 'active', '2020-05-30'),
('Avalanche', 'AVAX', 43114, 'PoS', 2, 'AVAX', 'active', '2020-09-21'),
('Cardano', 'ADA', NULL, 'PoS', 20, 'ADA', 'active', '2017-09-29'),
('Polkadot', 'DOT', NULL, 'NPoS', 6, 'DOT', 'active', '2020-05-26'),
('Arbitrum', 'ARB', 42161, 'PoS', 1, 'ETH', 'active', '2021-08-31'),
('Optimism', 'OP', 10, 'PoS', 2, 'ETH', 'active', '2021-12-16');

-- =====================================================
-- 2. USERS
-- =====================================================

INSERT INTO users (username, email, kyc_status, account_tier, country_code, registration_date, last_login, total_trades, total_volume_usd) VALUES
('crypto_whale_2024', 'whale@cryptoemail.com', 'verified', 'institutional', 'US', '2023-01-15 10:30:00', '2025-11-20 08:45:00', 1523, 15000000.00),
('hodl_master', 'hodler@cryptoemail.com', 'verified', 'premium', 'UK', '2023-03-22 14:20:00', '2025-11-19 22:30:00', 342, 890000.00),
('defi_trader_pro', 'defi@cryptoemail.com', 'verified', 'premium', 'SG', '2023-05-10 09:15:00', '2025-11-20 06:15:00', 892, 3500000.00),
('btc_maximalist', 'btc@cryptoemail.com', 'verified', 'basic', 'CA', '2023-07-05 16:45:00', '2025-11-18 12:00:00', 156, 250000.00),
('eth_enthusiast', 'eth@cryptoemail.com', 'verified', 'premium', 'DE', '2023-08-12 11:00:00', '2025-11-20 09:30:00', 678, 1800000.00),
('altcoin_hunter', 'altcoins@cryptoemail.com', 'verified', 'basic', 'AU', '2023-09-18 13:30:00', '2025-11-19 15:45:00', 234, 120000.00),
('day_trader_99', 'daytrader@cryptoemail.com', 'verified', 'premium', 'JP', '2023-10-25 08:00:00', '2025-11-20 10:00:00', 2145, 5600000.00),
('staking_rewards', 'staker@cryptoemail.com', 'verified', 'basic', 'FR', '2023-11-30 17:20:00', '2025-11-17 20:00:00', 89, 67000.00),
('nft_collector_pro', 'nfts@cryptoemail.com', 'verified', 'premium', 'AE', '2024-01-08 10:45:00', '2025-11-19 14:30:00', 445, 980000.00),
('yield_farmer_420', 'yieldfarm@cryptoemail.com', 'verified', 'basic', 'NL', '2024-02-14 12:00:00', '2025-11-20 07:00:00', 567, 450000.00),
('crypto_newbie', 'newbie@cryptoemail.com', 'pending', 'basic', 'US', '2024-11-01 09:00:00', '2025-11-20 08:00:00', 12, 5000.00),
('swing_trader_88', 'swing@cryptoemail.com', 'verified', 'premium', 'KR', '2024-03-20 15:30:00', '2025-11-19 18:20:00', 389, 720000.00),
('long_term_holder', 'longterm@cryptoemail.com', 'verified', 'basic', 'BR', '2024-04-15 11:15:00', '2025-11-15 10:00:00', 45, 150000.00),
('arbitrage_bot', 'arb@cryptoemail.com', 'verified', 'institutional', 'CH', '2024-05-10 08:30:00', '2025-11-20 10:15:00', 4523, 8900000.00),
('whale_alert_vip', 'vipwhale@cryptoemail.com', 'verified', 'institutional', 'SG', '2024-06-05 14:00:00', '2025-11-20 09:00:00', 892, 12000000.00);

-- =====================================================
-- 3. TOKENS
-- =====================================================

INSERT INTO tokens (code, name, ticker, blockchain_id, token_type, total_supply, circulating_supply, max_supply, decimals, contract_address, status, launch_date) VALUES
('BTC-native', 'Bitcoin', 'BTC', 2, 'native', 19500000, 19500000, 21000000, 8, NULL, 'active', '2009-01-03'),
('ETH-native', 'Ethereum', 'ETH', 1, 'native', 120000000, 120000000, NULL, 18, NULL, 'active', '2015-07-30'),
('0xdac17f958d2ee523a2206206994597c13d831ec7', 'Tether USD', 'USDT', 1, 'erc20', 95000000000, 95000000000, NULL, 6, '0xdac17f958d2ee523a2206206994597c13d831ec7', 'active', '2014-11-26'),
('BNB-native', 'BNB', 'BNB', 3, 'native', 155856000, 155856000, 200000000, 18, NULL, 'active', '2017-07-25'),
('SOL-native', 'Solana', 'SOL', 4, 'native', 450000000, 410000000, NULL, 9, NULL, 'active', '2020-03-16'),
('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'USD Coin', 'USDC', 1, 'erc20', 35000000000, 35000000000, NULL, 6, '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'active', '2018-09-26'),
('ADA-native', 'Cardano', 'ADA', 7, 'native', 45000000000, 35000000000, 45000000000, 6, NULL, 'active', '2017-09-29'),
('AVAX-native', 'Avalanche', 'AVAX', 6, 'native', 445000000, 375000000, 720000000, 18, NULL, 'active', '2020-09-21'),
('DOT-native', 'Polkadot', 'DOT', 8, 'native', 1400000000, 1280000000, NULL, 10, NULL, 'active', '2020-05-26'),
('MATIC-native', 'Polygon', 'MATIC', 5, 'native', 10000000000, 9300000000, 10000000000, 18, NULL, 'active', '2020-05-30'),
('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599', 'Wrapped Bitcoin', 'WBTC', 1, 'erc20', 155000, 155000, NULL, 8, '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599', 'active', '2019-01-30'),
('0x514910771af9ca656af840dff83e8264ecf986ca', 'Chainlink', 'LINK', 1, 'erc20', 1000000000, 550000000, 1000000000, 18, '0x514910771af9ca656af840dff83e8264ecf986ca', 'active', '2017-09-19'),
('0x1f9840a85d5af5bf1d1762f925bdaddc4201f984', 'Uniswap', 'UNI', 1, 'erc20', 1000000000, 753000000, 1000000000, 18, '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984', 'active', '2020-09-17'),
('0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0', 'Aave', 'AAVE', 1, 'erc20', 16000000, 14800000, 16000000, 18, '0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0', 'active', '2020-10-02'),
('0x6b175474e89094c44da98b954eedeac495271d0f', 'Dai Stablecoin', 'DAI', 1, 'erc20', 5200000000, 5200000000, NULL, 18, '0x6b175474e89094c44da98b954eedeac495271d0f', 'active', '2019-11-18'),
('ARB-native', 'Arbitrum', 'ARB', 9, 'native', 10000000000, 3000000000, 10000000000, 18, NULL, 'active', '2023-03-23'),
('OP-native', 'Optimism', 'OP', 10, 'native', 4294967296, 1100000000, 4294967296, 18, NULL, 'active', '2022-05-31'),
('0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'Wrapped Ether', 'WETH', 1, 'erc20', 3500000, 3500000, NULL, 18, '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2', 'active', '2017-12-19'),
('0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce', 'Shiba Inu', 'SHIB', 1, 'erc20', 999982000000000, 589000000000000, 999982000000000, 18, '0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce', 'active', '2020-08-01'),
('0x4d224452801aced8b2f0aebe155379bb5d594381', 'ApeCoin', 'APE', 1, 'erc20', 1000000000, 368000000, 1000000000, 18, '0x4d224452801aced8b2f0aebe155379bb5d594381', 'active', '2022-03-17');

-- =====================================================
-- 4. TOKEN METADATA
-- =====================================================

INSERT INTO token_metadata (token_id, description, website_url, category, market_cap_rank, coingecko_id) VALUES
(1, 'Bitcoin is a decentralized digital currency, without a central bank or single administrator.', 'https://bitcoin.org', 'Currency', 1, 'bitcoin'),
(2, 'Ethereum is a decentralized platform that runs smart contracts.', 'https://ethereum.org', 'Smart Contract Platform', 2, 'ethereum'),
(3, 'Tether is a stablecoin cryptocurrency pegged to the US dollar.', 'https://tether.to', 'Stablecoin', 3, 'tether'),
(4, 'BNB is the native cryptocurrency of the Binance exchange and BSC blockchain.', 'https://www.bnbchain.org', 'Exchange', 4, 'binancecoin'),
(5, 'Solana is a high-performance blockchain supporting builders around the world.', 'https://solana.com', 'Smart Contract Platform', 5, 'solana'),
(6, 'USDC is a fully collateralized US dollar stablecoin.', 'https://www.circle.com/usdc', 'Stablecoin', 6, 'usd-coin'),
(7, 'Cardano is a proof-of-stake blockchain platform.', 'https://cardano.org', 'Smart Contract Platform', 8, 'cardano'),
(8, 'Avalanche is a layer one blockchain that functions as a platform for DeFi.', 'https://www.avax.network', 'Smart Contract Platform', 9, 'avalanche-2'),
(9, 'Polkadot is a heterogeneous multi-chain interchange and translation architecture.', 'https://polkadot.network', 'Interoperability', 11, 'polkadot'),
(10, 'Polygon is a protocol for building Ethereum-compatible blockchain networks.', 'https://polygon.technology', 'Scaling', 13, 'matic-network'),
(11, 'Wrapped Bitcoin brings Bitcoin''s liquidity to Ethereum.', 'https://wbtc.network', 'Wrapped Token', 15, 'wrapped-bitcoin'),
(12, 'Chainlink is a decentralized oracle network.', 'https://chain.link', 'Oracle', 17, 'chainlink'),
(13, 'Uniswap is a leading decentralized crypto trading protocol.', 'https://uniswap.org', 'DeFi', 19, 'uniswap'),
(14, 'Aave is an open source and non-custodial liquidity protocol.', 'https://aave.com', 'DeFi', 23, 'aave'),
(15, 'DAI is a stablecoin cryptocurrency which aims to keep its value at one USD.', 'https://makerdao.com', 'Stablecoin', 25, 'dai'),
(16, 'Arbitrum is a Layer 2 scaling solution for Ethereum.', 'https://arbitrum.io', 'Scaling', 28, 'arbitrum'),
(17, 'Optimism is a Layer 2 scaling solution for Ethereum.', 'https://optimism.io', 'Scaling', 31, 'optimism'),
(18, 'Wrapped Ether is ERC-20 compatible version of ETH.', 'https://weth.io', 'Wrapped Token', 45, 'weth'),
(19, 'Shiba Inu is a decentralized meme token.', 'https://shibatoken.com', 'Meme', 18, 'shiba-inu'),
(20, 'ApeCoin is the ecosystem token for the APE ecosystem.', 'https://apecoin.com', 'NFT', 52, 'apecoin');

-- =====================================================
-- 5. TOKEN PRICE HISTORY (Recent 10 days of daily data for major tokens)
-- =====================================================

-- Bitcoin price history
INSERT INTO token_price_history (token_id, timestamp, open_price, high_price, low_price, close_price, volume_24h, volume_24h_usd, market_cap, price_change_24h, interval) VALUES
(1, '2025-11-11 00:00:00', 81876.54, 83456.78, 81543.21, 82543.21, 27890.12, 2302345678, 1610187600000, 0.81, '1d'),
(1, '2025-11-12 00:00:00', 82543.21, 84234.56, 82234.56, 83456.78, 29012.34, 2421234567, 1627675800000, 1.11, '1d'),
(1, '2025-11-13 00:00:00', 83456.78, 85123.45, 83123.45, 84234.56, 30123.45, 2537890123, 1642663400000, 0.93, '1d'),
(1, '2025-11-14 00:00:00', 84234.56, 85890.45, 83876.54, 84876.54, 28901.23, 2453456789, 1655156900000, 0.76, '1d'),
(1, '2025-11-15 00:00:00', 84876.54, 86543.21, 84543.21, 85543.21, 31234.56, 2672345678, 1668649400000, 0.79, '1d'),
(1, '2025-11-16 00:00:00', 85543.21, 87234.56, 85234.56, 86234.56, 32345.67, 2789012345, 1682641900000, 0.81, '1d'),
(1, '2025-11-17 00:00:00', 86234.56, 87890.45, 85876.54, 86876.54, 30123.45, 2617890123, 1695135400000, 0.74, '1d'),
(1, '2025-11-18 00:00:00', 86876.54, 88543.21, 86543.21, 87543.21, 31234.56, 2734567890, 1708127900000, 0.77, '1d'),
(1, '2025-11-19 00:00:00', 87543.21, 89234.56, 87234.56, 88234.56, 33456.78, 2952345678, 1721620400000, 0.79, '1d'),
(1, '2025-11-20 00:00:00', 88234.56, 89876.54, 87876.54, 88876.54, 34567.89, 3072345678, 1734112900000, 0.73, '1d');

-- Ethereum price history
INSERT INTO token_price_history (token_id, timestamp, open_price, high_price, low_price, close_price, volume_24h, volume_24h_usd, market_cap, price_change_24h, interval) VALUES
(2, '2025-11-11 00:00:00', 3467.89, 3545.67, 3456.78, 3512.34, 7789012.34, 27356789012, 421481000000, 1.28, '1d'),
(2, '2025-11-12 00:00:00', 3512.34, 3589.12, 3501.23, 3556.78, 8012345.67, 28489012345, 426815000000, 1.26, '1d'),
(2, '2025-11-13 00:00:00', 3556.78, 3634.56, 3545.67, 3601.23, 8234567.89, 29645678901, 432148000000, 1.25, '1d'),
(2, '2025-11-14 00:00:00', 3601.23, 3678.90, 3589.12, 3645.67, 7890123.45, 28767890123, 437482000000, 1.23, '1d'),
(2, '2025-11-15 00:00:00', 3645.67, 3723.45, 3634.56, 3689.12, 8123456.78, 29978901234, 442727000000, 1.19, '1d'),
(2, '2025-11-16 00:00:00', 3689.12, 3767.89, 3678.90, 3734.56, 8345678.90, 31156789012, 448061000000, 1.23, '1d'),
(2, '2025-11-17 00:00:00', 3734.56, 3812.34, 3723.45, 3778.90, 8012345.67, 30267890123, 453394000000, 1.19, '1d'),
(2, '2025-11-18 00:00:00', 3778.90, 3856.78, 3767.89, 3823.45, 8234567.89, 31489012345, 458728000000, 1.18, '1d'),
(2, '2025-11-19 00:00:00', 3823.45, 3901.23, 3812.34, 3867.89, 8567890.12, 33134567890, 464062000000, 1.16, '1d'),
(2, '2025-11-20 00:00:00', 3867.89, 3945.67, 3856.78, 3912.34, 8789012.34, 34378901234, 469396000000, 1.15, '1d');

-- Add latest price data for other tokens
INSERT INTO token_price_history (token_id, timestamp, open_price, high_price, low_price, close_price, volume_24h, volume_24h_usd, market_cap, price_change_24h, interval) VALUES
(3, '2025-11-20 00:00:00', 1.0000, 1.0002, 0.9998, 1.0001, 95000000000, 95000000000, 95000000000, 0.01, '1d'),
(4, '2025-11-20 00:00:00', 612.34, 625.67, 608.90, 619.45, 2345678.90, 1453456789, 96567890000, 1.16, '1d'),
(5, '2025-11-20 00:00:00', 143.56, 148.90, 142.34, 146.78, 8901234.56, 1306789012, 60180400000, 2.24, '1d'),
(6, '2025-11-20 00:00:00', 0.9999, 1.0001, 0.9997, 1.0000, 35000000000, 35000000000, 35000000000, 0.01, '1d'),
(7, '2025-11-20 00:00:00', 0.5678, 0.5823, 0.5623, 0.5789, 1234567890, 715123456, 20261500000, 1.95, '1d'),
(8, '2025-11-20 00:00:00', 34.56, 35.89, 34.12, 35.23, 5678901.23, 200123456, 13211250000, 1.94, '1d'),
(9, '2025-11-20 00:00:00', 6.78, 6.98, 6.71, 6.89, 234567890.12, 1616234567, 8819200000, 1.62, '1d'),
(10, '2025-11-20 00:00:00', 0.8934, 0.9156, 0.8823, 0.9012, 456789012.34, 411678901, 8381160000, 0.87, '1d'),
(11, '2025-11-20 00:00:00', 88543.21, 89876.54, 88234.56, 88876.54, 2345.67, 208456789, 13776164000, 0.38, '1d'),
(12, '2025-11-20 00:00:00', 15.67, 16.12, 15.54, 15.89, 23456789.01, 372789012, 8739500000, 1.40, '1d'),
(13, '2025-11-20 00:00:00', 9.87, 10.23, 9.76, 10.01, 34567890.12, 345978901, 7537530000, 1.42, '1d'),
(14, '2025-11-20 00:00:00', 298.45, 306.78, 296.34, 302.56, 1234567.89, 373567890, 4477888000, 1.38, '1d'),
(15, '2025-11-20 00:00:00', 0.9999, 1.0001, 0.9998, 1.0000, 5200000000, 5200000000, 5200000000, 0.01, '1d'),
(16, '2025-11-20 00:00:00', 1.23, 1.28, 1.21, 1.25, 345678901.23, 432098626, 3750000000, 1.63, '1d'),
(17, '2025-11-20 00:00:00', 2.34, 2.41, 2.32, 2.37, 234567890.12, 555965318, 2607000000, 1.28, '1d'),
(18, '2025-11-20 00:00:00', 3912.34, 3945.67, 3898.56, 3928.45, 456789.01, 1794567890, 13749575000, 0.41, '1d'),
(19, '2025-11-20 00:00:00', 0.00002134, 0.00002189, 0.00002112, 0.00002156, 8901234567890, 191934567, 12700400000, 1.03, '1d'),
(20, '2025-11-20 00:00:00', 1.45, 1.52, 1.43, 1.48, 123456789.01, 182716928, 544640000, 2.07, '1d');

-- =====================================================
-- 6. TOKEN VOLUME (Last 7 days for major tokens)
-- =====================================================

INSERT INTO token_volume (token_id, date, total_volume, total_volume_usd, buy_volume, sell_volume, trade_count, unique_traders, average_trade_size) VALUES
-- Bitcoin volumes
(1, '2025-11-20', 34567.89, 3072345678, 17890.12, 16677.77, 45678, 8934, 0.7567),
(1, '2025-11-19', 33456.78, 2952345678, 17234.56, 16222.22, 44567, 8723, 0.7512),
(1, '2025-11-18', 31234.56, 2734567890, 16123.45, 15111.11, 42345, 8456, 0.7378),
(1, '2025-11-17', 30123.45, 2617890123, 15567.89, 14555.56, 41234, 8234, 0.7304),
(1, '2025-11-16', 32345.67, 2789012345, 16678.90, 15666.77, 43567, 8567, 0.7425),
-- Ethereum volumes
(2, '2025-11-20', 8789012.34, 34378901234, 4567890.12, 4221122.22, 78901, 15678, 111.3456),
(2, '2025-11-19', 8567890.12, 33134567890, 4456789.01, 4111101.11, 76890, 15234, 111.4567),
(2, '2025-11-18', 8234567.89, 31489012345, 4234567.89, 4000000.00, 74567, 14890, 110.4321),
(2, '2025-11-17', 8012345.67, 30267890123, 4112345.67, 3900000.00, 73456, 14567, 109.1234),
(2, '2025-11-16', 8345678.90, 31156789012, 4323456.78, 4022222.12, 75678, 15012, 110.2890),
-- USDT volumes
(3, '2025-11-20', 95000000000, 95000000000, 48500000000, 46500000000, 234567, 45678, 404894.5123),
(3, '2025-11-19', 93000000000, 93000000000, 47500000000, 45500000000, 229345, 44567, 405612.3456),
(3, '2025-11-18', 91000000000, 91000000000, 46500000000, 44500000000, 224123, 43456, 406123.4567);

-- =====================================================
-- 7. TOKEN REVENUE
-- =====================================================

INSERT INTO token_revenue (token_id, date, revenue_type, amount, amount_usd, source, description) VALUES
-- Trading fees
(2, '2025-11-20', 'trading_fees', 12345.6789, 48312567, 'Uniswap', 'Trading fees collected from ETH pairs on Uniswap'),
(2, '2025-11-19', 'trading_fees', 11890.1234, 45678901, 'Uniswap', 'Trading fees collected from ETH pairs on Uniswap'),
(4, '2025-11-20', 'trading_fees', 8901.2345, 5512345, 'PancakeSwap', 'Trading fees from BNB pairs on PancakeSwap'),
(5, '2025-11-20', 'transaction_fees', 56789.0123, 8334567, 'Solana Network', 'Network transaction fees'),
-- Staking rewards
(2, '2025-11-20', 'staking_rewards', 45678.9012, 178678901, 'Lido', 'ETH staking rewards distributed to stakers'),
(7, '2025-11-20', 'staking_rewards', 890123.4567, 515123456, 'Cardano Network', 'ADA staking rewards'),
(8, '2025-11-20', 'staking_rewards', 23456.7890, 826789012, 'Avalanche Network', 'AVAX staking rewards'),
-- Token burns
(4, '2025-11-20', 'burn', 234.5678, 145234, 'Binance', 'Quarterly BNB token burn'),
(19, '2025-11-20', 'burn', 1000000000000, 21560000, 'Shiba Inu', 'Community-driven SHIB burn');

-- =====================================================
-- 8. EXCHANGES
-- =====================================================

INSERT INTO exchanges (name, type, country, website_url, api_available, trading_fee_percentage, volume_24h_usd, trust_score, status, launched_date) VALUES
('Binance', 'centralized', 'Malta', 'https://www.binance.com', true, 0.1000, 75000000000, 10, 'active', '2017-07-14'),
('Coinbase', 'centralized', 'United States', 'https://www.coinbase.com', true, 0.5000, 12000000000, 9, 'active', '2012-06-01'),
('Kraken', 'centralized', 'United States', 'https://www.kraken.com', true, 0.1600, 5000000000, 9, 'active', '2011-07-28'),
('Uniswap', 'decentralized', 'Global', 'https://uniswap.org', true, 0.3000, 2500000000, 8, 'active', '2018-11-02'),
('PancakeSwap', 'decentralized', 'Global', 'https://pancakeswap.finance', true, 0.2500, 1800000000, 7, 'active', '2020-09-20'),
('OKX', 'centralized', 'Seychelles', 'https://www.okx.com', true, 0.1000, 8000000000, 9, 'active', '2017-12-01'),
('Bybit', 'centralized', 'Dubai', 'https://www.bybit.com', true, 0.1000, 6500000000, 8, 'active', '2018-03-01'),
('KuCoin', 'centralized', 'Seychelles', 'https://www.kucoin.com', true, 0.1000, 3500000000, 8, 'active', '2017-09-15'),
('Huobi Global', 'centralized', 'Seychelles', 'https://www.huobi.com', true, 0.2000, 2800000000, 8, 'active', '2013-09-01'),
('SushiSwap', 'decentralized', 'Global', 'https://sushi.com', true, 0.3000, 800000000, 7, 'active', '2020-08-28');

-- =====================================================
-- 9. EXCHANGE LISTINGS
-- =====================================================

INSERT INTO exchange_listings (exchange_id, token_id, listing_date, is_active, volume_24h, volume_24h_usd) VALUES
-- Binance listings
(1, 1, '2017-07-14', true, 25678.90, 2282345678),
(1, 2, '2017-07-14', true, 6789012.34, 26545678901),
(1, 3, '2017-11-01', true, 45000000000, 45000000000),
(1, 4, '2017-07-25', true, 1456789.01, 902345678),
(1, 5, '2020-04-10', true, 4567890.12, 670234567),
-- Coinbase listings
(2, 1, '2012-06-01', true, 5678.90, 505678901),
(2, 2, '2016-05-21', true, 1234567.89, 4823456789),
(2, 3, '2018-11-05', true, 12000000000, 12000000000),
(2, 4, '2019-06-13', true, 234567.89, 145234567),
(2, 5, '2021-06-08', true, 890123.45, 130678901),
-- Uniswap DEX
(4, 2, '2018-11-02', true, 2345678.90, 9167890123),
(4, 6, '2020-09-01', true, 15000000000, 15000000000),
(4, 12, '2019-09-17', true, 5678901.23, 90234567),
(4, 13, '2020-09-17', true, 12345678.90, 123567890),
(4, 14, '2020-10-02', true, 234567.89, 70987654);

-- =====================================================
-- 10. TRADING PAIRS
-- =====================================================

INSERT INTO trading_pairs (exchange_id, base_token_id, quote_token_id, pair_symbol, current_price, volume_24h, volume_24h_usd, price_change_24h, bid_price, ask_price, spread_percentage, is_active) VALUES
-- Binance pairs
(1, 1, 3, 'BTC/USDT', 88876.54, 25678.90, 2282345678, 0.73, 88875.21, 88877.87, 0.0030, true),
(1, 2, 3, 'ETH/USDT', 3912.34, 6789012.34, 26545678901, 1.15, 3912.12, 3912.56, 0.0112, true),
(1, 4, 3, 'BNB/USDT', 619.45, 1456789.01, 902345678, 1.16, 619.43, 619.47, 0.0065, true),
(1, 5, 3, 'SOL/USDT', 146.78, 4567890.12, 670234567, 2.24, 146.76, 146.80, 0.0272, true),
(1, 2, 1, 'ETH/BTC', 0.0440, 345678.90, 1519234567, 0.42, 0.0440, 0.0441, 0.0227, true),
-- Coinbase pairs
(2, 1, 6, 'BTC/USDC', 88876.54, 5678.90, 505678901, 0.73, 88876.12, 88877.96, 0.0021, true),
(2, 2, 6, 'ETH/USDC', 3912.34, 1234567.89, 4823456789, 1.15, 3912.23, 3912.45, 0.0056, true),
(2, 4, 6, 'BNB/USDC', 619.45, 234567.89, 145234567, 1.16, 619.42, 619.48, 0.0097, true),
-- Uniswap pairs (DEX)
(4, 2, 6, 'ETH/USDC', 3912.34, 2345678.90, 9167890123, 1.15, 3911.89, 3912.79, 0.0230, true),
(4, 12, 2, 'LINK/ETH', 0.0041, 567890.12, 90234567, 0.25, 0.0041, 0.0041, 0.0244, true),
(4, 13, 2, 'UNI/ETH', 0.0026, 1234567.89, 123567890, 0.27, 0.0026, 0.0026, 0.0192, true);

-- =====================================================
-- 11. WALLETS
-- =====================================================

INSERT INTO wallets (user_id, wallet_address, blockchain_id, wallet_type, label, is_active) VALUES
(1, '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1', 1, 'non-custodial', 'Main Wallet', true),
(1, 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 2, 'hardware', 'Cold Storage', true),
(2, '0x8Ba1f109551bD432803012645Ac136ddd64DBA72', 1, 'non-custodial', 'Trading Wallet', true),
(3, '0x1234567890123456789012345678901234567890', 1, 'non-custodial', 'DeFi Wallet', true),
(3, 'DsUwMxDrhq8xn4Nzz9vGLW6WrGvhCqxJtBMq2X5Hq2T1', 4, 'non-custodial', 'Solana Main', true),
(4, 'bc1qa5wkgaew2dkv56kfvj49j0av5nml45x9ek9hz6', 2, 'hardware', 'BTC Only', true),
(5, '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd', 1, 'non-custodial', 'ETH Holder', true),
(6, '0xaabbccddaabbccddaabbccddaabbccddaabbccdd', 1, 'custodial', 'Exchange Wallet', true),
(7, '0x9876543210987654321098765432109876543210', 1, 'non-custodial', 'Day Trading', true),
(8, 'addr1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh', 7, 'non-custodial', 'Cardano Staking', true),
(9, '0xfedcbafedcbafedcbafedcbafedcbafedcbafed', 1, 'non-custodial', 'NFT Wallet', true),
(10, '0x1111222233334444555566667777888899990000', 1, 'custodial', 'Yield Farming', true),
(11, '0x0000111122223333444455556666777788889999', 1, 'custodial', 'Newbie Wallet', true),
(12, 'HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH', 4, 'non-custodial', 'Solana Trading', true),
(13, '0xaaaa1111bbbb2222cccc3333dddd4444eeee5555', 1, 'hardware', 'Long Term Hold', true),
(14, '0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef', 1, 'non-custodial', 'Arbitrage Bot', true),
(15, '0xcafebabecafebabecafebabecafebabecafebabe', 1, 'non-custodial', 'VIP Wallet', true);

-- =====================================================
-- 12. WALLET BALANCES
-- =====================================================

INSERT INTO wallet_balances (wallet_id, token_id, balance, available_balance, locked_balance) VALUES
-- Whale's balances
(1, 2, 5234.56789012, 5000.00000000, 234.56789012),
(1, 3, 8500000.00, 8500000.00, 0.00),
(2, 1, 125.45678901, 125.45678901, 0.00),
-- HODL master
(3, 1, 8.56789012, 7.56789012, 1.00000000),
(3, 2, 345.67890123, 300.00000000, 45.67890123),
-- DeFi trader
(4, 2, 890.12345678, 800.00000000, 90.12345678),
(4, 6, 1250000.00, 1250000.00, 0.00),
(4, 13, 25000.00000000, 20000.00000000, 5000.00000000),
-- BTC maximalist
(6, 1, 3.45678901, 3.45678901, 0.00),
-- ETH enthusiast
(7, 2, 456.78901234, 456.78901234, 0.00),
(7, 12, 5000.00000000, 4500.00000000, 500.00000000),
-- Altcoin hunter
(8, 5, 850.12345678, 800.00000000, 50.12345678),
(8, 7, 150000.00000000, 150000.00000000, 0.00),
-- Day trader
(9, 2, 1234.56789012, 1000.00000000, 234.56789012),
(9, 3, 2500000.00, 2500000.00, 0.00),
(9, 4, 4500.00000000, 4000.00000000, 500.00000000),
-- Staking rewards
(10, 7, 95000.00000000, 0.00000000, 95000.00000000),
(10, 8, 2000.00000000, 0.00000000, 2000.00000000),
-- NFT collector
(11, 2, 234.56789012, 200.00000000, 34.56789012),
(11, 20, 100000.00000000, 100000.00000000, 0.00000000),
-- Yield farmer
(12, 14, 500.00000000, 0.00000000, 500.00000000),
(12, 6, 450000.00, 450000.00, 0.00),
-- Newbie
(13, 1, 0.05678901, 0.05678901, 0.00),
(13, 2, 1.23456789, 1.23456789, 0.00);

-- =====================================================
-- 13. TOKEN HOLDINGS (Snapshots)
-- =====================================================

INSERT INTO token_holdings (user_id, token_id, snapshot_date, total_balance, balance_usd, average_buy_price, unrealized_pnl, realized_pnl) VALUES
-- Latest holdings (today)
(1, 2, '2025-11-20', 5234.56789012, 20474567.89, 3500.00, 2157234.56, 450000.00),
(1, 3, '2025-11-20', 8500000.00, 8500000.00, 1.00, 0.00, 0.00),
(2, 1, '2025-11-20', 8.56789012, 761234.56, 82000.00, 58901.23, 12000.00),
(2, 2, '2025-11-20', 345.67890123, 1352345.67, 3400.00, 177123.45, 34567.89),
(3, 2, '2025-11-20', 890.12345678, 3482345.67, 3600.00, 277890.12, 89012.34),
(3, 6, '2025-11-20', 1250000.00, 1250000.00, 1.00, 0.00, 0.00),
(4, 1, '2025-11-20', 3.45678901, 307234.56, 85000.00, 13456.78, 0.00),
(5, 2, '2025-11-20', 456.78901234, 1787123.45, 3700.00, 96890.12, 23456.78),
(6, 5, '2025-11-20', 850.12345678, 124789.01, 135.00, 10012.34, 2345.67),
(7, 2, '2025-11-20', 1234.56789012, 4829456.78, 3500.00, 509123.45, 123456.78),
(8, 7, '2025-11-20', 95000.00000000, 54995500.00, 0.50, 9505000.00, 0.00),
-- Historical snapshot (1 week ago)
(1, 2, '2025-11-13', 5234.56789012, 18867890.12, 3500.00, 1378901.23, 450000.00),
(2, 1, '2025-11-13', 8.56789012, 721456.78, 82000.00, 19123.45, 12000.00),
(3, 2, '2025-11-13', 890.12345678, 3205678.90, 3600.00, 98567.89, 89012.34);

-- =====================================================
-- 14. TRANSACTIONS
-- =====================================================

INSERT INTO transactions (user_id, from_wallet_id, to_wallet_id, token_id, transaction_type, amount, price_per_token, total_value_usd, fee, fee_usd, transaction_hash, blockchain_id, exchange_id, status, timestamp) VALUES
-- Recent buy transactions
(1, NULL, 1, 2, 'buy', 50.00000000, 3867.89, 193394.50, 0.15000000, 580.18, '0xabc123def456ghi789jkl012mno345pqr678stu901vwx234yz', 1, 1, 'completed', '2025-11-19 14:30:00'),
(2, NULL, 3, 1, 'buy', 0.25000000, 87543.21, 21885.80, 0.00025000, 21.89, '0x111222333444555666777888999000aaabbbcccdddeeefff000', 2, 2, 'completed', '2025-11-19 10:15:00'),
(3, NULL, 4, 2, 'buy', 100.00000000, 3823.45, 382345.00, 0.30000000, 1147.04, '0x123abc456def789ghi012jkl345mno678pqr901stu234vwx567', 1, 1, 'completed', '2025-11-18 16:45:00'),
-- Sell transactions
(7, 9, NULL, 2, 'sell', 25.00000000, 3912.34, 97808.50, 0.07500000, 293.43, '0xfedcba9876543210fedcba9876543210fedcba9876543210fedc', 1, 1, 'completed', '2025-11-20 09:00:00'),
(5, 7, NULL, 12, 'sell', 500.00000000, 15.89, 7945.00, 1.50000000, 23.84, '0x999888777666555444333222111000fffeeedddc
ccbbbaaa9998', 1, 2, 'completed', '2025-11-19 11:30:00'),
-- Transfer transactions
(1, 1, 3, 3, 'transfer', 100000.00, 1.00, 100000.00, 5.00, 5.00, '0xabcdef1234567890abcdef1234567890abcdef1234567890abcd', 1, NULL, 'completed', '2025-11-18 13:20:00'),
(15, 16, 4, 6, 'transfer', 50000.00, 1.00, 50000.00, 2.50, 2.50, '0x1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z', 1, NULL, 'completed', '2025-11-17 10:45:00'),
-- Swap transactions (DEX)
(3, 4, 4, 2, 'swap', 10.00000000, 3734.56, 37345.60, 0.03000000, 112.04, '0xswap1234567890abcdefswap1234567890abcdefswap12345678', 1, 4, 'completed', '2025-11-17 15:30:00'),
(10, 12, 12, 14, 'swap', 50.00000000, 298.45, 14922.50, 0.15000000, 44.77, '0xswapabcdef1234567890swapabcdef1234567890swapabcdef12', 1, 4, 'completed', '2025-11-16 12:00:00'),
-- Staking transactions
(8, 10, NULL, 7, 'stake', 50000.00000000, 0.5678, 28390.00, 0.00000000, 0.00, '0xstake123456789abcdefstake123456789abcdefstake1234567', 7, NULL, 'completed', '2025-11-15 09:00:00'),
(8, 10, NULL, 8, 'stake', 1000.00000000, 34.56, 34560.00, 0.00000000, 0.00, '0xstakeabcdef123456789stakeabcdef123456789stakeabcdef1', 6, NULL, 'completed', '2025-11-14 14:30:00'),
-- Pending transactions
(11, 13, NULL, 2, 'buy', 0.50000000, 3912.34, 1956.17, 0.00150000, 5.87, '0xpending123456789abcdefpending123456789abcdefpending12', 1, 2, 'pending', '2025-11-20 10:30:00');

-- =====================================================
-- 15. STAKING RECORDS
-- =====================================================

INSERT INTO staking_records (user_id, token_id, staked_amount, staking_period_days, apr_percentage, rewards_earned, rewards_earned_usd, start_date, end_date, status) VALUES
-- Active staking
(8, 7, 95000.00000000, NULL, 4.5000, 1234.56789012, 714.67, '2025-10-15 09:00:00', NULL, 'active'),
(8, 8, 2000.00000000, 90, 8.7500, 43.21098765, 1521.34, '2025-11-01 14:30:00', NULL, 'active'),
(2, 2, 45.67890123, NULL, 3.2500, 0.12345678, 482.56, '2025-09-20 10:00:00', NULL, 'active'),
(10, 14, 500.00000000, 180, 12.5000, 8.56789012, 2592.34, '2025-08-15 11:00:00', NULL, 'active'),
(13, 7, 5000.00000000, 30, 3.5000, 14.38356164, 8.32, '2025-11-10 16:00:00', NULL, 'active'),
-- Completed staking
(5, 2, 100.00000000, 90, 4.0000, 0.98630137, 3856.78, '2025-08-01 10:00:00', '2025-10-30 10:00:00', 'completed'),
(12, 8, 500.00000000, 60, 7.5000, 6.16438356, 216.78, '2025-09-15 12:00:00', '2025-11-14 12:00:00', 'completed'),
-- Withdrawn
(6, 7, 20000.00000000, 60, 4.2500, 139.72602740, 80.89, '2025-09-01 09:00:00', '2025-10-31 09:00:00', 'withdrawn');

-- =====================================================
-- 16. LIQUIDITY POOLS
-- =====================================================

INSERT INTO liquidity_pools (pool_name, protocol, blockchain_id, token_a_id, token_b_id, token_a_reserve, token_b_reserve, total_liquidity_usd, volume_24h_usd, fee_percentage, apy_percentage, is_active) VALUES
('ETH-USDC', 'Uniswap V3', 1, 2, 6, 1234567.89012345, 4823456789.01, 9646913578, 2456789012, 0.3000, 12.4500, true),
('ETH-USDT', 'Uniswap V3', 1, 2, 3, 2345678.90123456, 9178901234.56, 18357802469, 3567890123, 0.3000, 11.8900, true),
('BTC-USDT', 'PancakeSwap V2', 3, 11, 3, 12345.67890123, 1097234567.89, 2194469136, 892345678, 0.2500, 8.7600, true),
('ETH-BTC', 'Uniswap V3', 1, 2, 11, 234567.89012345, 2.98765432, 1835678901, 456789012, 0.3000, 9.3400, true),
('BNB-USDT', 'PancakeSwap V2', 3, 4, 3, 1234567.89, 764567890.12, 1529135780, 567890123, 0.2500, 14.5600, true),
('SOL-USDC', 'Raydium', 4, 5, 6, 4567890.12, 670234567.89, 1340469136, 345678901, 0.2500, 18.9000, true),
('AVAX-USDC', 'Trader Joe', 6, 8, 6, 1234567.89, 43456789.01, 86913578, 123456789, 0.3000, 15.6700, true),
('MATIC-USDC', 'QuickSwap', 5, 10, 6, 12345678.90, 11123456.78, 22246914, 89012345, 0.3000, 13.4500, true),
('LINK-ETH', 'Uniswap V2', 1, 12, 2, 567890.12, 23.45, 182901234, 45678901, 0.3000, 11.2300, true),
('UNI-ETH', 'Uniswap V2', 1, 13, 2, 1234567.89, 3.21, 25056789, 12345678, 0.3000, 9.8900, true);

-- =====================================================
-- DATA VALIDATION
-- =====================================================

-- Count records in each table
SELECT 'blockchains' as table_name, COUNT(*) as record_count FROM blockchains
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'tokens', COUNT(*) FROM tokens
UNION ALL SELECT 'token_metadata', COUNT(*) FROM token_metadata
UNION ALL SELECT 'token_price_history', COUNT(*) FROM token_price_history
UNION ALL SELECT 'token_volume', COUNT(*) FROM token_volume
UNION ALL SELECT 'token_revenue', COUNT(*) FROM token_revenue
UNION ALL SELECT 'wallets', COUNT(*) FROM wallets
UNION ALL SELECT 'wallet_balances', COUNT(*) FROM wallet_balances
UNION ALL SELECT 'token_holdings', COUNT(*) FROM token_holdings
UNION ALL SELECT 'exchanges', COUNT(*) FROM exchanges
UNION ALL SELECT 'exchange_listings', COUNT(*) FROM exchange_listings
UNION ALL SELECT 'trading_pairs', COUNT(*) FROM trading_pairs
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL SELECT 'staking_records', COUNT(*) FROM staking_records
UNION ALL SELECT 'liquidity_pools', COUNT(*) FROM liquidity_pools
ORDER BY table_name;
