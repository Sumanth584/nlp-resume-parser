export const RegisterCompany = (companyname, email, password, hrname, about) => {
    return async dispatch => {
        try {
            const response = await fetch('/api/register-company', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ companyname, email, password, hrname, about })
            });

            if (!response.ok) {
                throw new Error('Error registering company');
            }

            const resData = await response.json();
            dispatch({
                type: "REGISTER_COMPANY",
                uid: resData.data.id, // Assuming the ID is returned in the response
                data: resData.data
            });
        } catch (error) {
            throw error;
        }
    }
};
