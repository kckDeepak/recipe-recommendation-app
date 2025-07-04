const chai = require('chai');
const chaiHttp = require('chai-http');
const app = require('../server');
const { expect } = chai;

chai.use(chaiHttp);

describe('Recipe API', () => {
  it('should return recipes for valid ingredients', (done) => {
    chai.request(app)
      .get('/api/recipes/search?ingredients=chicken,tomatoes')
      .end((err, res) => {
        expect(res).to.have.status(200);
        expect(res.body).to.be.an('array');
        done();
      });
  });

  it('should return recipe details for valid ID', (done) => {
    chai.request(app)
      .get('/api/recipes/12345') // Replace 12345 with a known recipe ID
      .end((err, res) => {
        expect(res).to.have.status(200);
        expect(res.body).to.have.property('title');
        expect(res.body).to.have.property('instructions');
        done();
      });
    });

  it('should return recommendations', (done) => {
    chai.request(app)
      .get('/api/recipes/recommend?ingredients=chicken,tomatoes')
      .end((err, res) => {
        expect(res).to.have.status(200);
        expect(res.body).to.be.an('array');
        done();
      });
  });
});