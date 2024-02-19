import * as solanaWeb3 from '@solana/web3.js';
import base58 from 'bs58'


document.addEventListener('DOMContentLoaded', async function() {
    // Set testing to true if running in a local environment
    const testing = false;
    let TOKENID = "G9GQFWQmTiBzm1Hh4gM4ydQB4en3wPUxBZ1PS8DruXy8";
    let supply = 100000;
    let balance = 0;

    if (testing) {
        TOKENID = "9YZ2syoQHvMeksp4MYZoYMtLyFWkkyBgAsVuuJzSZwVu";
        supply = 17 * 1000000000;
    }


    // Initialize Solana connection
    const solana = window.solana;
    if (!solana || !solana.isPhantom) {
        alert('Phantom wallet not detected. Please install Phantom and try again.');
        return;
    }

    // Prompt user to connect wallet
    try {
        await solana.connect();
        console.log('Wallet connected:', solana.publicKey.toString());
        // Get token balance
        // Connect to https://api.metaplex.solana.com/
        const connection = new solanaWeb3.Connection('https://api.metaplex.solana.com/');
        const publicKey = new solanaWeb3.PublicKey(solana.publicKey.toString());
        const sol_balance = await connection.getBalance(publicKey);
        console.log('Balance:', sol_balance/solanaWeb3.LAMPORTS_PER_SOL, 'SOL');        
        
        // Add your actual program ID here
        const TOKEN_PROGRAM_ID = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA';

        async function getTokenAccountBalance(wallet, solanaConnection) {
            const filters = [
                {
                    dataSize: 165,    // size of account (bytes)
                },
                {
                    memcmp: {
                        offset: 32,     // location of our query in the account (bytes)
                        bytes: wallet,  // our search criteria, a base58 encoded string
                    },
                }
            ];
            const accounts = await solanaConnection.getParsedProgramAccounts(
                new solanaWeb3.PublicKey(TOKEN_PROGRAM_ID),
                { filters: filters }
            );
            console.log(`Found ${accounts.length} token account(s) for wallet ${wallet}.`);
            let balance = 0;
            for (const account of accounts) {
                const parsedAccountInfo = account.account.data;
                const mintAddress = parsedAccountInfo["parsed"]["info"]["mint"];
                const tokenBalance = parsedAccountInfo["parsed"]["info"]["tokenAmount"]["uiAmount"];
                if (mintAddress === TOKENID) {
                    console.log('Found our token account:', account.pubkey.toString());
                    console.log('Balance:', tokenBalance);
                    balance = tokenBalance;
                    break; // Exit the loop after finding the balance
                }
            }
            return balance;
        }
        function formatNumber(value) {
            const suffixes = ["", "K", "M", "B", "T"];
            const suffixNum = Math.floor(("" + value).length / 3);
            let shortValue = parseFloat((suffixNum !== 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(2));
            if (shortValue % 1 !== 0) {
                shortValue = shortValue.toFixed(1);
            }
            return shortValue + suffixes[suffixNum];
        }
        
        var balancePromise = getTokenAccountBalance(publicKey, connection);
        balancePromise.then((output) => {
            const percent_of_votes = (output / supply) * 100;
            const roundedOutput = output > 10 ? Math.round(output) : output;
            const roundedPercent = percent_of_votes > 5 ? Math.round(percent_of_votes) : percent_of_votes;

            const formattedOutput = formatNumber(roundedOutput);

            document.getElementById('balance').textContent = formattedOutput;
            document.getElementById('percent').textContent = roundedPercent.toString();
            balance = output;
        });
    } catch (error) {
        console.error('Error connecting wallet:', error);
        alert('Error connecting wallet. Check the console for details.');
        return;
    }

    document.getElementById('signMessageForm').addEventListener('submit', async function(event) {
        event.preventDefault();
        const vote = document.getElementById('vote').value.trim(); // Get the value of the vote input field
        
        // Ensure the vote is not empty
        if (!vote) {
            alert('Please enter your vote.');
            return;
        }

        // Encode the message as a buffer-like object
        const messageUint8Array = new TextEncoder().encode(vote);
        // Request signature from Phantom
        try {
            const { public_key, signature } = await solana.request({
                method: 'signMessage',
                params: {
                    message: messageUint8Array,
                    display: "utf8"
                },
            });

            const url = 'http://localhost:5000/vote'; // Update the URL as needed

            // Convert signature to readable format
            const sig = base58.encode(signature);

            
            console.log(sig);


            window.location.href = `/vote?message=${encodeURIComponent(vote)}&signature=${encodeURIComponent(sig)}&walletAddress=${encodeURIComponent(solana.publicKey.toBase58())}&votes=${encodeURIComponent(balance)}&percent=${encodeURIComponent((balance / supply) * 100)}`

        } catch (error) {
            console.error('Error submitting vote:', error);
            alert('Error submitting vote. Check the console for details.');
        }
    });
});
