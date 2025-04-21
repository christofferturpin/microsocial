# What is MicroSocial?
MicroSocial is a lightweight, retro-inspired, serverless social media platform where each user gets exactly one page. No feed, no dopamine drip. Just your thoughts, your manifesto, your weird poem about frogs, or a shrine to your favorite Game Boy glitch. Like GeoCities and MySpace had a baby and raised it on cloud infrastructure.

Each user gets:

* One page, public and permanent.
* A web-based HTML/CSS editor that saves your content to S3 via a secure, serverless API.
* A 5-member "webring" list, letting you link to your favorite other users' pages.
* No likes, comments, or stats. Just retro vibes.
	
Built on:

* AWS Lambda + API Gateway for compute.
* DynamoDB for data persistence. 
* Cloudfront + S3 for static page hosting and content delivery. 
* Cognito for user auth.
	
# Features

* Static HTML pages generated and uploaded automatically per user
  
* Retro aesthetics inspired by 90s/2000s internet culture.

* XSS protection at application layer & CSP headers.
  
* Discover section pulls random live pages from the ring
  
* Fully serverless using SAM (Serverless Application Model)
  
* Supports cursed gifs, weird fonts, audio embeds, all that fun stuff.


# Installation

1) Clone this repo.
2) Deply via AWS SAM:
```
sam build
sam deploy --guided
```
4) run create_and_inject_sec_headers.py
5) Upload frontend assets to S3. 



# Design Philosophy
The internet is boring, lets make it less boring by using todays super cool tools. And lets do this for cheap, because baby - I'm broke. 

The idea is that instead of scaling for virality, we scale for intentionality and personality. Instead of trying to be the next Twitter killer (Twitter seems to be doing that itself), MicroSocial gives you one page. Just one. A single HTML file you fully control. No feeds. No likes. No ad-driven dopamine economy. It’s the opposite of infinite scroll; it’s a cul-de-sac. A weird, handmade webpage with room for bad poetry and blinking gifs.

It’s not built for hype. It’s built for meaning. But it's not built poorly, every thing runs serverlessly on AWS, meaning no single points of failure. You could onboard 10 users or 10,000 and the infra wouldn’t blink (and if it does we just do some DAX and SQS and call that a feature). 

It’s a little weird. A little overengineered. And entirely yours.


# Technical Architecture (For Curious Nerds & Hiring Managers)


## Auth
Auth is handled via Amazon Cognito using a hosted UI and implicit grant flow.

Upon successful login, users are redirected with an access_token in the URL hash.

We parse this client-side and store the token in localStorage.

Lambda authorizers validate the token before any sensitive endpoint is reached (/edit, /me).

## API & Lambda
All logic is split across 3 core Lambdas:
* /edit: Authenticated POST that updates a user’s page in DynamoDB and writes the corresponding HTML file to S3.

* /me: Authenticated GET that returns the user’s saved content + webring links.

* /random: Public GET that lists and samples user pages directly from S3.

## Data Storage
A single table named Pages, keyed on userId, stores:

* content: The user’s raw text.

* webring: An optional array of up to 5 linked usernames.

* lastUpdated: ISO timestamp, for good measure.

If we wanted to we could scale this database out as new users onboard and old users update their pages to add future functionality. 

## Static Site Hosting: S3 + CloudFront

Every user’s page is compiled into HTML via Lambda and uploaded to an S3 bucket at:

s3://microsocial-site-<account-id>/u/<username>.html

This bucket is fronted by CloudFront with Origin Access Control to restrict direct S3 access.

Each edit triggers a CloudFront invalidation for the individual page, so users see changes instantly. Given the general desire to see what one has made, the action of the user visiting their recently posted page caches it for quick delivery. 
	
## XSS Filtering: In Lambda & Via CSP 
1. Frontline Defense: Content-Security-Policy (CSP)
All user-generated pages (/u/*) are served through CloudFront with a strict CSP:
```
default-src 'self';
script-src 'none';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com;
frame-src https://www.youtube.com https://www.youtube-nocookie.com;
object-src 'none';
base-uri 'none';
```

This blocks:

* Inline and external scripts

* Dangerous embeds and object tags

* JavaScript execution entirely (even sneaky stuff like onerror=)

2. Server-Side Sanity Check (Lambda)
On submit, the /edit Lambda does a lightweight tag check — just enough to reject truly cursed HTML (like <script> or <iframe>).
		
## Frontend: HTML, JS, CSS--

The editor and viewer are designed as a single-page app.
JS handles.
* Token parsing + routing
* Fetching/saving page content by calling Lambdas with OAC. 
* Rendering webring + discover links
* Discover functionality pulls random S3 keys, strips u/, and links them on the homepage.
		
## Why Serverless?

MicroSocial is powered entirely by AWS Serverless technologies. This decision was made early and intentionally, not just for cost-efficiency but to maximize scalability, reduce operational overhead, and stay true to the ethos of minimalism that the project itself promotes. Users only get one page; I should only need one pipeline.
	
By using AWS SAM, I could define the infrastructure as code and deploy it with a single command. The stack includes:


## Why Not Just Use a CMS?

Because I’m not building Medium. MicroSocial isn't about monetized likes, infinite feeds, or analytics dashboards. It’s about control. I wanted users to have a single page, like in the old web, a chunk of HTML they could claim. You don’t need a CMS for that. You need Lambda, some permissions, and a little respect for the craft.

	
## License
MIT. Because information wants to be free.

## TODO that I may get to. 
1. Chatbot that allows users to generate HTML and screws with them slightly.
2. Messaging.
3. "My Vibe" section.
4. More monitoring.
5. SEO.

