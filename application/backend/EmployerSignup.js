import React, { useState } from 'react';
import { Button, Input } from 'antd';
import TextArea from 'antd/lib/input/TextArea';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

function EmployerSignup() {
    const [company, setCompany] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [hrname, setHrname] = useState("");
    const [about, setAbout] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        try {
            setLoading(true);
            // TODO: Implement the logic to send data to the backend
            // await dispatch(RegisterCompany(company, email, password, hrname, about));
            setLoading(false);
            toast.success("Account created Successfully. Redirecting to home page...", {
                position: "top-right",
                autoClose: 3000,
            });

            // Redirect to the onboarding/homepage
            window.location.href = '/onboarding'; 
        } catch (err) {
            setLoading(false);
            toast.error(err.message, {
                position: "top-right",
                autoClose: 3000,
            });
        }
    };

    return (
        <div style={{ fontFamily: "Montserrat" }}>
            <ToastContainer />
            <div style={{ padding: '2rem' }}>
                <form onSubmit={handleSubmit}>
                    <h3>Sign Up as an Employer</h3>
                    <Input placeholder="Company Name" onChange={e => setCompany(e.target.value)} required />
                    <Input placeholder="Email" type="email" onChange={e => setEmail(e.target.value)} required />
                    <Input placeholder="Password" type="password" onChange={e => setPassword(e.target.value)} required />
                    <Input placeholder="HR Name" onChange={e => setHrname(e.target.value)} />
                    <TextArea placeholder="About Company" onChange={e => setAbout(e.target.value)} />
                    <Button type="submit" loading={loading} style={{ marginTop: '1rem' }}>Submit</Button>
                </form>
            </div>
        </div>
    );
}

export default EmployerSignup;
