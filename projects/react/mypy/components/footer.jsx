import reactLogo from '../src/assets/react.svg'
import '../styles/stock.css'

export default function Footer() {
    return (
        <footer>
            <p>&copy; 2024 MyPy App. All Rights Reserved.</p>
            <p>Powered by
                <a href="https://react.dev" target="_blank">
                <img src={reactLogo} className="my-footer-logo react" alt="React logo"/>
                </a>
            </p>
        </footer>
    )
}