import React, { useState, useRef, useEffect } from 'react';
import { Send, Plane, Map } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

// Components
const FlightCard = ({ data }) => {
    if (!data) return null;
    return (
        <div className="flight-card">
            <div className="flight-segment">
                <div className="flight-route">
                    <span>{data.Departure}</span>
                    <span className="arrow">→</span>
                    <span>{data.Arrival}</span>
                </div>
                <div>{data.Duration}</div>
            </div>
            <div className="flight-segment" style={{ color: '#8696a0', fontSize: '0.8rem' }}>
                {data['Flight Number']} • {data['Number of Stops']} stop(s)
            </div>
            <div className="flight-segment" style={{ color: '#8696a0', fontSize: '0.8rem' }}>
                Dep: {new Date(data['Departure Time']).toLocaleString()}
            </div>
            <div className="flight-price">{data.Price}</div>
        </div>
    )
}

function App() {
    const [messages, setMessages] = useState([
        { role: 'bot', text: 'Hello! I am your AI Travel Agent. How can I help you today?', data: [] }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = { role: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: userMsg.text })
            });

            if (!res.ok) throw new Error("Network error");

            const data = await res.json();
            const botMsg = {
                role: 'bot',
                text: data.response,
                data: data.data // Array of flight offers
            };
            setMessages(prev => [...prev, botMsg]);
        } catch (e) {
            setMessages(prev => [...prev, { role: 'bot', text: "Sorry, I encountered an error connecting to the server." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app-container">
            {/* Sidebar */}
            <div className="sidebar">
                <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Plane size={24} color="#00a884" /> Travel Agent
                </h2>
                <div style={{ marginTop: '2rem', color: '#8696a0' }}>
                    <p><Map size={16} style={{ display: 'inline', verticalAlign: 'middle' }} /> Flight Search</p>
                    <p>More features coming soon...</p>
                </div>
            </div>

            {/* Chat Area */}
            <div className="chat-area">
                <div className="messages" ref={scrollRef}>
                    {messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.role}`}>
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                            {msg.data && msg.data.length > 0 && (
                                <div style={{ marginTop: '10px' }}>
                                    {msg.data.map((offer, i) => (
                                        <FlightCard key={i} data={offer} />
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                    {loading && <div className="message bot">Thinking...</div>}
                </div>

                <div className="input-area">
                    <input
                        className="input-box"
                        placeholder="Type a message..."
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleSend()}
                    />
                    <button className="send-btn" onClick={handleSend}>
                        <Send size={24} />
                    </button>
                </div>
            </div>
        </div>
    )
}

export default App
