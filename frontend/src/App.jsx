import { useState } from "react";


export default function App() {
const [messages, setMessages] = useState([
{ role: "system", content: "👋 Hi! I’m TravelGPT. Where do you want to go?" }
]);
const [input, setInput] = useState("");
const [loading, setLoading] = useState(false);


const sendMessage = async () => {
if (!input.trim()) return;
const userMsg = { role: "user", content: input };
setMessages([...messages, userMsg]);
setInput("");
setLoading(true);
try {
const resp = await fetch("http://localhost:4000/api/conversation", {
method: "POST",
headers: { "Content-Type": "application/json" },
body: JSON.stringify({ message: input })
});
const data = await resp.json();
setMessages(m => [...m, userMsg, { role: "assistant", content: data.reply }]);
} catch (err) {
setMessages(m => [...m, { role: "assistant", content: "⚠️ Error talking to backend." }]);
} finally {
setLoading(false);
}
};


return (
<div className="flex flex-col h-screen max-w-md mx-auto">
<div className="flex-1 overflow-y-auto p-4 space-y-2">
{messages.map((msg, i) => (
<div key={i} className={`p-2 rounded-xl ${msg.role === "user" ? "bg-blue-500 text-white self-end" : "bg-gray-200 text-gray-800 self-start"}`}>
{msg.content}
</div>
))}
{loading && <div className="italic text-gray-500">TravelGPT is typing…</div>}
</div>
<div className="p-2 flex border-t">
<input
value={input}
onChange={e => setInput(e.target.value)}
onKeyDown={e => e.key === "Enter" && sendMessage()}
placeholder="Type your travel plan..."
className="flex-1 border rounded-xl px-3 py-2 mr-2"
/>
<button onClick={sendMessage} className="bg-blue-600 text-white rounded-xl px-4 py-2">Send</button>
</div>
</div>
);
}