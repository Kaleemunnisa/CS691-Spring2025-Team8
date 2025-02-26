'use strict';

const { createCoreController } = require('@strapi/strapi').factories;

module.exports = createCoreController('api::category.category', ({ strapi }) => ({
  async find(ctx) {
    const { data, meta } = await super.find(ctx);

    // Transform response to include `attributes` wrapper
    const formattedData = data.map((item) => ({
      id: item.id,
      attributes: { ...item }
    }));

    return { data: formattedData, meta };
  }
}));
