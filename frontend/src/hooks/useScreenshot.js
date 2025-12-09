import { useCallback } from 'react';
import html2canvas from 'html2canvas';

/**
 * Hook for capturing chart screenshots
 * Uses html2canvas to capture the current chart state
 */
export function useScreenshot() {
    const captureChart = useCallback(async (chartContainerRef) => {
        if (!chartContainerRef || !chartContainerRef.current) {
            console.error('Chart container ref not available');
            return null;
        }

        try {
            const canvas = await html2canvas(chartContainerRef.current, {
                backgroundColor: '#1e222d',
                scale: 2, // Higher quality
                logging: false,
                useCORS: true,
                allowTaint: true,
            });

            // Convert to base64
            const imageData = canvas.toDataURL('image/png');
            return imageData;
        } catch (error) {
            console.error('Failed to capture screenshot:', error);
            return null;
        }
    }, []);

    const saveScreenshot = useCallback(async (imageData, tradeId, url) => {
        if (!imageData) return null;
        
        // Default to journal trades screenshot endpoint if no URL provided
        const targetUrl = url || 'http://localhost:9000/api/trades/screenshot';

        try {
            const response = await fetch(targetUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    trade_id: tradeId,
                    image: imageData,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to save screenshot');
            }

            const result = await response.json();
            return result.path;
        } catch (error) {
            console.error('Failed to save screenshot:', error);
            return null;
        }
    }, []);

    return {
        captureChart,
        saveScreenshot
    };
}
