import React, { useState, useEffect } from 'react';
import { Target, AlertTriangle, Shield, TrendingUp, DollarSign, Settings as SettingsIcon, Trash2 } from 'lucide-react';
import { fetchChallenge, updateChallenge } from '../services/api';
import './AccountPage.css';

export default function AccountPage() {
    const [loading, setLoading] = useState(true);
    const [accountConfig, setAccountConfig] = useState({
        balance: 50000,
        riskPerTrade: 0.5,
        minRR: 2.0,
        maxConcurrent: 2,
        leverage: 100,
        accountType: 'step1',
        newsTrading: true,
        copyTrading: false,
        profitTargetStep1: 8,
        profitTargetStep2: 6,
        dailyLossLimit: 5,
        totalLossLimit: 10,
        minTradingDays: 4,
        inactivityLimit: 10
    });

    const [currentBalance, setCurrentBalance] = useState(50000);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const challenge = await fetchChallenge(1); // Default challenge ID

            setCurrentBalance(challenge.current_balance);

            setAccountConfig(prev => ({
                ...prev,
                balance: challenge.starting_balance,
                riskPerTrade: challenge.risk_per_trade,
                maxConcurrent: challenge.max_positions,
                accountType: challenge.phase === 'Phase1' ? 'step1' : challenge.phase === 'Phase2' ? 'step2' : 'funded',
                profitTargetStep1: challenge.profit_target,
                dailyLossLimit: challenge.daily_loss_limit,
                totalLossLimit: challenge.max_drawdown,
                // Keep other fields local for now or add to backend later
            }));
        } catch (err) {
            console.error("Failed to load settings:", err);
            // Fallback to local storage if API fails
            const saved = localStorage.getItem('smc-account-config');
            if (saved) setAccountConfig(JSON.parse(saved));
        } finally {
            setLoading(false);
        }
    };

    // Challenge Progress - calculate from current settings
    // Profit target is a percentage (8% for Step 1, 6% for Step 2)
    const profitTargetPct = accountConfig.accountType === 'step1'
        ? accountConfig.profitTargetStep1
        : accountConfig.profitTargetStep2;

    const progress = {
        currentBalance: currentBalance,
        startingBalance: accountConfig.balance,
        profitTargetPct: profitTargetPct,
        profitTargetAmount: accountConfig.balance * (profitTargetPct / 100), // Calculate dollar amount
        currentProfit: currentBalance - accountConfig.balance,
        currentProfitPct: ((currentBalance - accountConfig.balance) / accountConfig.balance) * 100,
        dailyLoss: Math.max(0, accountConfig.balance - currentBalance), // Drawdown from starting
        dailyLossLimit: accountConfig.balance * (accountConfig.dailyLossLimit / 100),
        totalLoss: Math.max(0, accountConfig.balance - currentBalance), // Total drawdown
        totalLossLimit: accountConfig.balance * (accountConfig.totalLossLimit / 100),
    };

    const profitProgress = progress.currentProfit > 0
        ? (progress.currentProfit / progress.profitTargetAmount) * 100
        : 0;
    const dailyLossProgress = (progress.dailyLoss / progress.dailyLossLimit) * 100;
    const totalLossProgress = (progress.totalLoss / progress.totalLossLimit) * 100;

    const handleSave = async () => {
        try {
            const updateData = {
                starting_balance: accountConfig.balance,
                current_balance: accountConfig.balance, // Reset current balance to match starting balance
                risk_per_trade: accountConfig.riskPerTrade,
                max_positions: accountConfig.maxConcurrent,
                phase: accountConfig.accountType === 'step1' ? 'Phase1' : accountConfig.accountType === 'step2' ? 'Phase2' : 'Funded',
                profit_target: accountConfig.profitTargetStep1,
                daily_loss_limit: accountConfig.dailyLossLimit,
                max_drawdown: accountConfig.totalLossLimit
            };

            await updateChallenge(1, updateData);
            setCurrentBalance(accountConfig.balance); // Update local state
            localStorage.setItem('smc-account-config', JSON.stringify(accountConfig)); // Backup
            alert('✅ Account settings saved to backend!');
            // Reload to show updated data
            await loadSettings();
        } catch (err) {
            console.error("Failed to save settings:", err);
            alert('❌ Failed to save settings');
        }
    };

    if (loading) {
        return <div className="loading-container">Loading Settings...</div>;
    }

    return (
        <div className="account-page-modern">
            {/* Challenge Status */}
            <div className="challenge-status-modern">
                <div className="status-header-modern">
                    <div>
                        <h2>Challenge Status: Step 1</h2>
                        <span className="status-badge-modern active">Active</span>
                    </div>
                    <button className="delete-challenge-btn">
                        <Trash2 size={16} />
                        Delete Challenge
                    </button>
                </div>

                <div className="progress-cards-modern">
                    <div className="progress-card-modern success">
                        <div className="progress-header-modern">
                            <Target size={20} />
                            <span>Profit Target</span>
                        </div>
                        <div className="progress-value-modern">
                            ${progress.currentProfit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })} / ${progress.profitTargetAmount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                        </div>
                        <div className="progress-bar-modern">
                            <div className="progress-fill-modern" style={{ width: `${Math.min(profitProgress, 100)}%` }}></div>
                        </div>
                        <div className="progress-meta-modern">
                            {profitProgress.toFixed(1)}% Complete • Target: ${(progress.startingBalance + progress.profitTargetAmount).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                        </div>
                    </div>

                    <div className="progress-card-modern warning">
                        <div className="progress-header-modern">
                            <AlertTriangle size={20} />
                            <span>Daily Loss</span>
                        </div>
                        <div className="progress-value-modern">
                            ${progress.dailyLoss.toLocaleString()} / ${progress.dailyLossLimit.toLocaleString()}
                        </div>
                        <div className="progress-bar-modern">
                            <div className="progress-fill-modern" style={{ width: `${dailyLossProgress}%` }}></div>
                        </div>
                        <div className="progress-meta-modern">
                            {dailyLossProgress.toFixed(1)}% Used • {accountConfig.dailyLossLimit}% Limit
                        </div>
                    </div>

                    <div className="progress-card-modern danger">
                        <div className="progress-header-modern">
                            <Shield size={20} />
                            <span>Total Drawdown</span>
                        </div>
                        <div className="progress-value-modern">
                            ${progress.totalLoss.toLocaleString()} / ${progress.totalLossLimit.toLocaleString()}
                        </div>
                        <div className="progress-bar-modern">
                            <div className="progress-fill-modern" style={{ width: `${totalLossProgress}%` }}></div>
                        </div>
                        <div className="progress-meta-modern">
                            {totalLossProgress.toFixed(1)}% Used • {accountConfig.totalLossLimit}% Limit
                        </div>
                    </div>
                </div>
            </div>

            {/* Account Configuration */}
            <div className="account-config-modern">
                <h3><SettingsIcon size={20} /> Account Settings</h3>

                <div className="settings-grid-modern">
                    {/* Starting Balance */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <DollarSign size={16} />
                            <span>Starting Balance</span>
                        </div>
                        <input
                            type="number"
                            value={accountConfig.balance}
                            onChange={(e) => setAccountConfig({ ...accountConfig, balance: Number(e.target.value) })}
                            className="setting-input-modern"
                        />
                    </div>

                    {/* Risk per Trade */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <TrendingUp size={16} />
                            <span>Risk per Trade (%)</span>
                        </div>
                        <input
                            type="number"
                            step="0.1"
                            value={accountConfig.riskPerTrade}
                            onChange={(e) => setAccountConfig({ ...accountConfig, riskPerTrade: Number(e.target.value) })}
                            className="setting-input-modern"
                        />
                    </div>

                    {/* Minimum R:R */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <Target size={16} />
                            <span>Minimum R:R</span>
                        </div>
                        <input
                            type="number"
                            step="0.1"
                            value={accountConfig.minRR}
                            onChange={(e) => setAccountConfig({ ...accountConfig, minRR: Number(e.target.value) })}
                            className="setting-input-modern"
                        />
                    </div>

                    {/* Max Concurrent Trades */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <Shield size={16} />
                            <span>Max Concurrent Trades</span>
                        </div>
                        <input
                            type="number"
                            value={accountConfig.maxConcurrent}
                            onChange={(e) => setAccountConfig({ ...accountConfig, maxConcurrent: Number(e.target.value) })}
                            className="setting-input-modern"
                        />
                    </div>

                    {/* Leverage */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <TrendingUp size={16} />
                            <span>Leverage</span>
                        </div>
                        <select
                            value={accountConfig.leverage}
                            onChange={(e) => setAccountConfig({ ...accountConfig, leverage: Number(e.target.value) })}
                            className="setting-select-modern"
                        >
                            <option value={100}>1:100</option>
                            <option value={50}>1:50</option>
                            <option value={30}>1:30</option>
                        </select>
                    </div>

                    {/* Account Type */}
                    <div className="setting-item-modern">
                        <div className="setting-label-modern">
                            <SettingsIcon size={16} />
                            <span>Account Type</span>
                        </div>
                        <select
                            value={accountConfig.accountType}
                            onChange={(e) => setAccountConfig({ ...accountConfig, accountType: e.target.value })}
                            className="setting-select-modern"
                        >
                            <option value="step1">Step 1 (8% target)</option>
                            <option value="step2">Step 2 (6% target)</option>
                            <option value="funded">Funded</option>
                        </select>
                    </div>
                </div>

                {/* Toggle Settings */}
                <div className="toggle-settings-modern">
                    <div className="toggle-item-modern">
                        <div className="toggle-label-modern">
                            <span>News Trading</span>
                            <small>Allow trading during news events</small>
                        </div>
                        <label className="toggle-switch-modern">
                            <input
                                type="checkbox"
                                checked={accountConfig.newsTrading}
                                onChange={(e) => setAccountConfig({ ...accountConfig, newsTrading: e.target.checked })}
                            />
                            <span className="toggle-slider-modern"></span>
                        </label>
                    </div>

                    <div className="toggle-item-modern">
                        <div className="toggle-label-modern">
                            <span>Copy Trading</span>
                            <small>Internal copy trading (if available)</small>
                        </div>
                        <label className="toggle-switch-modern">
                            <input
                                type="checkbox"
                                checked={accountConfig.copyTrading}
                                onChange={(e) => setAccountConfig({ ...accountConfig, copyTrading: e.target.checked })}
                            />
                            <span className="toggle-slider-modern"></span>
                        </label>
                    </div>
                </div>

                <button className="save-btn-modern" onClick={handleSave}>
                    Save Configuration
                </button>
            </div>

            {/* Challenge Rules */}
            <div className="challenge-rules-modern">
                <h3>Challenge Rules</h3>
                <div className="rules-grid-modern">
                    <div className="rule-item-modern">
                        <label>Step 1 Target (%)</label>
                        <input
                            type="number"
                            value={accountConfig.profitTargetStep1}
                            onChange={(e) => setAccountConfig({ ...accountConfig, profitTargetStep1: Number(e.target.value) })}
                        />
                    </div>
                    <div className="rule-item-modern">
                        <label>Step 2 Target (%)</label>
                        <input
                            type="number"
                            value={accountConfig.profitTargetStep2}
                            onChange={(e) => setAccountConfig({ ...accountConfig, profitTargetStep2: Number(e.target.value) })}
                        />
                    </div>
                    <div className="rule-item-modern">
                        <label>Daily Loss Limit (%)</label>
                        <input
                            type="number"
                            value={accountConfig.dailyLossLimit}
                            onChange={(e) => setAccountConfig({ ...accountConfig, dailyLossLimit: Number(e.target.value) })}
                        />
                    </div>
                    <div className="rule-item-modern">
                        <label>Total Loss Limit (%)</label>
                        <input
                            type="number"
                            value={accountConfig.totalLossLimit}
                            onChange={(e) => setAccountConfig({ ...accountConfig, totalLossLimit: Number(e.target.value) })}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
