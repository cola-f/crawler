"use strict";
require('dotenv').config();

const request = require('request');
const uuidv4 = require("uuid/v4");
const sign = require('jsonwebtoken').sign

const access_key = process.env.access_key_upbit;
console.log(access_key)
const secret_key = process.env.secret_key_upbit;
const server_url = "https://api.upbit.com"

const payload = {
	access_key: access_key,
	nonce: uuidv4(),
}

const token = sign(payload, secret_key)

const options = {
	metho: "GET",
	url: server_url + "/v1/accounts",
	headers: {Authorization: `Bearer ${token}`},
};

request(options, (error, response, body) => {
	if(error) throw new Error(error)
	console.log(body);
});
