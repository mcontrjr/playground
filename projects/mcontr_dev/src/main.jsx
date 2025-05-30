import { useState } from 'react';
import coolImg from './assets/man_with_dog.jpg';
import Footer from '../components/footer';
import { Box, createTheme, Paper, ThemeProvider } from '@mui/material'; 


// Create a custom theme for the app
const theme = createTheme({
  typography: {
      fontFamily: '"Roboto Mono", monospace',
      h2: {
          color: "#ffffff" // Custom color for h2
      },
      h3: {
          color: "#ffffff" // Custom color for h3
      },
      body1: {
          color: "#ffffff" // Custom default text color
      }
  },
  palette: {
    mode: 'dark',
    primary: {
      main: '#fdf5e9',
    },
    secondary: {
      main: '#924d21',
      contrastText: 'rgba(74,15,15,0.87)',
    },
    background: {
      paper: '#001a25',
      default: '#011823',
    },
  },
  spacing: 10,
});


function Head() {
  return (
    <ThemeProvider theme={theme}>
      <header>
        <h1>MyPy</h1>
        <nav>
          <a href="/info" className='my-button'>Server Info</a>
        </nav>
      </header>
    </ThemeProvider>
  )
}

function About() {
  return (
    <section id="desc">
        <div className="my-container">
            <div className="row">
                <div className="text-center">
                    <h1 className="display-4">What's this about?</h1>
                    <p className="lead">
                        This started with the hope to build a quick web app but is quickly turning into something very different...
                        Now it's becoming a website with some features and things that I find kinda cool but they are mostly dumb, and that's okay.
                        For now check out a sick picture I found of this guy and his dawg.
                    </p>
                    <hr className="my-4"/>
                    <img src={coolImg} className='custom-img'/>
                </div>
            </div>
        </div>
    </section>
  )
}

function Feature({title, body, route}) {
  return (
    <ThemeProvider theme={theme}>
      <Box >
          <a href={route}>
              <div >
                  <h5>{title}</h5>
                  <p>{body}</p>
              </div>
          </a>
      </Box>
    </ThemeProvider>
    // <div className='my-col-3 my-card'>
    //   <a href={route} className="my-card">
    //       <div className="my-card-body">
    //           <h5 className="my-card-title">{title}</h5>
    //           <p>{body}</p>
    //       </div>
    //   </a>
    // </div>
  )
}

function MyFeatures() {
  return (
    <section id="features">
      <div className='my-container'>
        <h1>Playground</h1>
        <div className='my-row'>
          <Feature route={"/guess"} title={"Guessing Game"} body={"Go try to guess a number. See if you can get it in 1 attempt -- it's definitely possible!"}/>
          <Feature route={"/weather"} title={"What's the weather?"} body={"Check local weather from server but also your own."}/>
          <Feature route={"/random"} title={"Image Generator"} body={"Genuinely some random ass pictures from IDK where but it's fun! See if you get a cool one!"}/>
        </div>
      </div>
    </section>
  )
}

function MyTools() {
  return (
    <section id="tools">
      <div className='my-container'>
        <h1>Tools</h1>
        <div className='my-row'>
          <Feature route={"/finance"} title={"Parser"} body={"Figure out where your money is going!"}/>
        </div>
      </div>
    </section>
  )
}

export default function MainPage() {

  return (
    <>
      <ThemeProvider theme={theme}>
        <Paper />
          <Head />
          <About />
          <MyFeatures />
          <MyTools />
          <Footer />
        <Paper />
      </ThemeProvider>
    </>
  )
}

