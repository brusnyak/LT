import React, { createContext, useContext, useState, useEffect } from 'react';

const MarketContext = createContext();

export function MarketProvider({ children }) {
    const [pair, setPair] = useState(() => localStorage.getItem('smc-pair') || 'EURUSD');
    const [timeframe, setTimeframe] = useState(() => localStorage.getItem('smc-timeframe') || 'M5');
    const [strategy, setStrategy] = useState(() => localStorage.getItem('smc-strategy') || 'range_4h');
    const [dataSource, setDataSource] = useState(() => localStorage.getItem('smc-datasource') || 'csv');

    useEffect(() => {
        localStorage.setItem('smc-pair', pair);
    }, [pair]);

    useEffect(() => {
        localStorage.setItem('smc-timeframe', timeframe);
    }, [timeframe]);

    useEffect(() => {
        localStorage.setItem('smc-strategy', strategy);
    }, [strategy]);

    useEffect(() => {
        localStorage.setItem('smc-datasource', dataSource);
    }, [dataSource]);

    return (
        <MarketContext.Provider value={{
            pair, setPair,
            timeframe, setTimeframe,
            strategy, setStrategy,
            dataSource, setDataSource
        }}>
            {children}
        </MarketContext.Provider>
    );
}

export function useMarket() {
    return useContext(MarketContext);
}

export default MarketContext;
