# CENG495 ASSIGNMENT 1

Cloud Market is an e-commerce Web application which is deployed to Vercel. It uses MongoDB as its NoSQL database.

## Tech Stack

Flask-python is used for the backend. Because its the framework that I have experience with the most. I have used it for couple of internships before. 

For the frontend, Flask's default frontend, Jinja2 html renderer, is relied on. I used these because I thought we are not required to write a modern frontend. Jinja was perfect for this homework as its simple and clean.

## Usage

### New user registeration

A new user can be registered with the register button on top right corner of the home page.

### Login

Already signed up users can log in from the log in button on right of the navigation bar of the home page.

Admin user can enter with admin username and password which are currently being "admin" and "admin495", respectively.

### Home page and Items

The items can be browsed in the home page whether a user logged in or not. Everyone can see the reviews and ratings and item details, too. Users can choose the category of the items that they want to filter in the home page.

But only the logged in users can add ratings or reviews. ALso, users can delete their own ratings or reviews.

### User page

All users have their own user pages in which they contain their user information. Their username, role, average ratings are presented there.

Users can browse other users profiles thru their names on reviews and ratings.

### Admin Dashboard

Thru admin dashboards admins can create and delete users and items. PLEASE DO NOT DELETE ADMINS.

## Backend & MongoDB Design Decisions

In the backend, I wrote 4 services for modularity. They are being admin service, authorization service, rating service and review service.

In MongoDB, I used 2 collections. One for users and one for items. In users collection, I store username, hashed password, is_admin, reviews (array), average rating and creation date. In items collection, I store item details. But bear in mind that, in order to utilize MongoDB's flexibility I dont store the unnecessary features for the specific categories.

When an item gets deleted, their reviews and ratings on users are deleted, too. When a user gets deleted, their reviews and ratings on any items get deleted also.

Only admins can create new items. Only admins can remove items and users.

I hold both reviews and ratings under one field named "reviews" in both items and users. But I divided "reviews" to two subfields. One being the "rating" and second being the "content" which is the review comment. When a rating is given, the "rating" subfield of "reviews" is filled. If only the review comment is given then I hold them in "content" subfield of the rating. I designed like this in order to utilize MongoDB's stretchability.